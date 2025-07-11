import SPiiPlusPython as sp
import pipython


class StageController:
    def __init__(self, stage_port, stage_baud=115200):
        self.hc = sp.OpenCommSerial(stage_port, stage_baud)


class MotionController:
    def __init__(self, stage_port=1, stage_baud=115200, hexapod_port=4, hexapod_baud=115200):
        # Initialize stage
        self.hc = sp.OpenCommSerial(stage_port, stage_baud)

        # Initialize hexapod
        self.hexapod = pipython.GCS2Device("C-887")
        self.hexapod.ConnectRS232(hexapod_port, hexapod_baud)


    ### STAGES ###
    def zero_stage(self):
        sp.RunBuffer(self.hc, 1, "STARTUP", sp.SYNCHRONOUS, True)

    def move_stage_to_point(self, axis, point, velocity=20, endVelocity=0):
        sp.ExtToPoint(
            self.hc,
            sp.MotionFlags.ACSC_AMF_VELOCITY,
            getattr(sp.Axis, f"ACSC_AXIS_{axis.upper()}"),
            point,
            velocity=velocity,
            endVelocity=endVelocity,
            wait=sp.SYNCHRONOUS,
            failure_check=True
        )

    def get_stage_pos(self):
        x_pos = sp.GetTargetPosition(self.hc, 0, sp.SYNCHRONOUS)
        y_pos = sp.GetTargetPosition(self.hc, 1, sp.SYNCHRONOUS)
        return x_pos, y_pos
    
    def close_stage(self):
        sp.DisableAll(self.hc, sp.SYNCHRONOUS, True)
        sp.CloseComm(self.hc)


    ### HEXAPOD ###
    def zero_hexapod(self):
        axes = ['X', 'Y', 'Z', 'U', 'V', 'W']
        for axis in axes:
            self.hexapod.MOV(axis, 0)

    def move_hexapod(self, axis, position):
        self.hexapod.MOV(axis, position)

    def get_hexapod_pos(self):
        return self.hexapod.qPOS(['X', 'Y', 'Z', 'U', 'V', 'W'])

    def close_hexapod(self):
        self.hexapod.CloseConnection()