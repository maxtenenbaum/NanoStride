import numpy as np
import nidaqmx
from nidaqmx.constants import AcquisitionType, Edge
import time
import threading
import queue

# --- DAQ Parameters ---
fs = 2_000_000  # 2 MS/s (Sample Rate)
# For 7.91 kHz trigger rate, each burst duration is ~126.4 us.
# At 2 MS/s, that's 126.4 us * 2 samples/us = ~252 samples per burst.
# Let's target num_samples_per_trigger based on this.
samples_per_trigger = 126 # Example: A nice round number of samples per burst

# Number of distinct segments to output from the master waveform
# This defines the total finite duration.
TOTAL_BURSTS_TO_OUTPUT = 14000 # Output 500 triggered bursts

# Define the maximum number of waveform segments to pre-queue in Python (FIFO depth)
MAX_WAVEFORMS_IN_QUEUE = 20 # Increased buffer for better robustness at higher trigger rates

# --- Master Waveform Generation (Unique Signal with Activity Indicator) ---
# This will be generated once.
# It should be long enough to provide all segments needed for TOTAL_BURSTS_TO_OUTPUT.
total_master_samples = TOTAL_BURSTS_TO_OUTPUT * samples_per_trigger
master_waveform_time = np.arange(total_master_samples) / fs

# --- Design for Visual Activity and Uniqueness ---
# We'll create a segment with two parts:
# 1. A short, high-amplitude 'sync pulse' at the very beginning of each segment
# 2. A more complex, evolving signal for the rest of the segment.

# Define the sync pulse: a very short, strong positive pulse
sync_pulse_duration = 5e-6 # 5 us pulse
sync_pulse_samples = int(sync_pulse_duration * fs)
if sync_pulse_samples == 0: sync_pulse_samples = 1 # Ensure at least one sample
sync_pulse_amplitude = 5.0 # High amplitude for visibility (ensure within DAQ limits)

# Ensure samples_per_trigger is large enough to contain the sync pulse
if sync_pulse_samples >= samples_per_trigger:
    raise ValueError("sync_pulse_samples must be less than samples_per_trigger")

# Generate the main evolving part of the master waveform
# (same as before, but ensure it occupies the remaining samples in each segment)
freq1 = 5_000   # 5 kHz
freq2 = 25_000  # 25 kHz
freq3 = 70_000  # 70 kHz

master_waveform_main = (
    1.5 * np.sin(2 * np.pi * freq1 * master_waveform_time) +
    0.8 * np.sin(2 * np.pi * freq2 * master_waveform_time + np.pi/4) +
    0.3 * np.sin(2 * np.pi * freq3 * master_waveform_time + np.pi/2)
)

# Normalize the main part to a reasonable amplitude (e.g., within +/- 1.5V)
max_main_val = np.max(np.abs(master_waveform_main))
if max_main_val > 0:
    master_waveform_main = master_waveform_main / max_main_val * 1.5 # Scale to +/- 1.5V


# Now, assemble the final master waveform by embedding the sync pulse into each segment
master_waveform = np.zeros(total_master_samples)
for i in range(TOTAL_BURSTS_TO_OUTPUT):
    segment_start_idx = i * samples_per_trigger
    segment_end_idx = segment_start_idx + samples_per_trigger

    # Embed sync pulse
    sync_pulse_segment_start = segment_start_idx
    sync_pulse_segment_end = segment_start_idx + sync_pulse_samples
    master_waveform[sync_pulse_segment_start:sync_pulse_segment_end] = sync_pulse_amplitude

    # Embed main signal (after the sync pulse)
    main_signal_start = segment_start_idx + sync_pulse_samples
    main_signal_end = segment_end_idx
    master_waveform[main_signal_start:main_signal_end] = master_waveform_main[main_signal_start:main_signal_end]

# Make sure the master waveform values are within your DAQ's voltage limits (e.g., -10V to 10V)
# We scaled to max 5V for sync pulse, which should be fine.

print(f"Generated master waveform: {len(master_waveform)} samples, duration {total_master_samples / fs:.4f} s")
print(f"Each triggered burst will output {samples_per_trigger} samples.")
print(f"Total finite bursts to output: {TOTAL_BURSTS_TO_OUTPUT}")
print(f"Total theoretical run time: {TOTAL_BURSTS_TO_OUTPUT * (samples_per_trigger / fs):.4f} s (if triggers are continuous)")


# --- Waveform Generation (Producer Thread) ---
def waveform_producer(data_queue, stop_event, master_waveform_data, samples_per_segment, total_bursts):
    current_offset = 0
    bursts_produced = 0
    total_samples_master = len(master_waveform_data)

    print("Producer: Starting to slice master waveform...")

    while not stop_event.is_set() and bursts_produced < total_bursts:
        end_offset = current_offset + samples_per_segment

        # If we reach the theoretical end of the master waveform segments
        if bursts_produced >= total_bursts:
            break # Exit loop once all segments are produced

        segment = master_waveform_data[current_offset:end_offset]

        try:
            data_queue.put(segment, timeout=0.1) # Shorter timeout for faster feedback
            # print(f"Producer: Queued burst {bursts_produced + 1}/{total_bursts}. Queue size: {data_queue.qsize()}")
            current_offset = end_offset
            bursts_produced += 1
        except queue.Full:
            pass # Keep trying
        except Exception as e:
            print(f"Producer Error: {e}")
            stop_event.set()
        time.sleep(0.0001) # Very small delay to allow context switching

    print(f"Producer: Finished producing {bursts_produced} bursts.")
    # Signal that no more data will be produced.
    # A special 'None' or empty object can be used as a sentinel if needed,
    # but for finite tasks, simply not putting more data is enough for the consumer
    # to eventually empty the queue and recognize completion.


# --- DAQmx Output (Consumer Thread) ---
def daqmx_consumer(ao_task, data_queue, stop_event, total_bursts):
    bursts_completed = 0
    print("Consumer: Waiting for waveform segments in queue and triggers...")

    while not stop_event.is_set() and bursts_completed < total_bursts:
        try:
            # Wait for the current output to complete and the task to re-arm
            # Or for a timeout if no trigger arrives for a long time
            ao_task.wait_until_done(timeout=1.0) # Allows checking stop_event

            # Check if producer is done AND queue is empty
            if not producer_thread.is_alive() and data_queue.empty():
                print("Consumer: Producer finished and queue is empty. Initiating shutdown.")
                stop_event.set() # Signal main loop and producer to stop fully
                break

            # Get the next waveform segment from the queue. Block if the queue is empty.
            next_waveform_segment = data_queue.get(timeout=1.0)
            # print(f"Consumer: Got segment from queue for burst {bursts_completed + 1}. Remaining: {data_queue.qsize()}")

            ao_task.stop()
            ao_task.write(next_waveform_segment)
            ao_task.start()
            bursts_completed += 1
            # print(f"Consumer: Task re-armed for burst {bursts_completed}. Waiting for next trigger.")

        except queue.Empty:
            # Queue is empty. Check if producer is still alive to produce more.
            if not producer_thread.is_alive():
                print("Consumer: Queue is empty and producer has finished. All bursts processed or no more data.")
                stop_event.set() # Signal to stop
                break
            # print("Consumer: Queue empty, waiting for producer...")
            time.sleep(0.01)
        except nidaqmx.errors.DaqError as e:
            if e.error_code == -200284: # Task not running (e.g., before first start)
                time.sleep(0.01)
            elif e.error_code == -200015: # Timeout on wait_until_done
                pass # Still waiting for trigger, no problem
            else:
                print(f"Consumer DAQmx Error: {e}")
                stop_event.set()
        except Exception as e:
            print(f"Consumer Error: {e}")
            stop_event.set()

    print(f"Consumer: Completed {bursts_completed} bursts out of {total_bursts}.")
    stop_event.set() # Ensure all threads are signaled to stop when done

# --- Main Program ---
if __name__ == "__main__":
    data_queue = queue.Queue(maxsize=MAX_WAVEFORMS_IN_QUEUE)
    stop_event = threading.Event()

    producer_thread = threading.Thread(
        target=waveform_producer,
        args=(data_queue, stop_event, master_waveform, samples_per_trigger, TOTAL_BURSTS_TO_OUTPUT)
    )
    producer_thread.daemon = True
    producer_thread.start()

    with nidaqmx.Task() as ao_task:
        ao_task.ao_channels.add_ao_voltage_chan("PXI1Slot6/ao1")
        ao_task.timing.cfg_samp_clk_timing(
            rate=fs,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=samples_per_trigger
        )

        trigger_source = '/PXI1Slot2/PFI0' # Verify your trigger source
        ao_task.triggers.start_trigger.cfg_dig_edge_start_trig(
            trigger_source=trigger_source,
            trigger_edge=Edge.FALLING # Or RISING, matching your external trigger
        )
        ao_task.triggers.start_trigger.retriggerable = True

        print("Main: Waiting for initial waveform segment from producer...")
        try:
            initial_waveform_segment = data_queue.get(timeout=5.0)
        except queue.Empty:
            print("Error: Producer did not put initial waveform in queue within timeout. Exiting.")
            stop_event.set()
            producer_thread.join()
            exit()

        ao_task.write(initial_waveform_segment, auto_start=False)

        consumer_thread = threading.Thread(target=daqmx_consumer, args=(ao_task, data_queue, stop_event, TOTAL_BURSTS_TO_OUTPUT))
        consumer_thread.daemon = True
        consumer_thread.start()

        ao_task.start()
        print(f"Main: DAQ task armed and waiting for first trigger on {trigger_source}.")
        print(f"System will output {TOTAL_BURSTS_TO_OUTPUT} unique bursts, each {samples_per_trigger} samples long.")
        print("Look for the high-amplitude sync pulse at the start of each burst on the oscilloscope.")
        print("Press Enter to stop early, or wait for all bursts to complete.\n")

        try:
            # Keep main thread alive until stop_event is set by consumer or user
            while not stop_event.is_set():
                time.sleep(0.1) # Don't busy-wait
            print("Main: Stop event received, program shutting down.")
        except KeyboardInterrupt:
            print("\nMain: KeyboardInterrupt detected.")
        finally:
            print("Main: Stopping all tasks...")
            stop_event.set()
            producer_thread.join(timeout=2.0)
            consumer_thread.join(timeout=2.0)
            if producer_thread.is_alive():
                print("Warning: Producer thread did not stop gracefully.")
            if consumer_thread.is_alive():
                print("Warning: Consumer thread did not stop gracefully.")
            ao_task.stop()
            print("Main: Program terminated.")