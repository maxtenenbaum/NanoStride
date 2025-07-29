import SPiiPlusPython as sp
import pipython


class StageController:
    def __init__(self, stage_port, stage_baud=115200):
        self.hc = sp.OpenCommSerial(stage_port, stage_baud)

    def zero_stage(self):
        sp.RunBuffer(self.hc, 1, "STARTUP", sp.SYNCHRONOUS, True)
    
    def close_stage(self):
        sp.DisableAll(self.hc, sp.SYNCHRONOUS, True)
        sp.CloseComm(self.hc)
        
    def get_stage_pos(self):
        x_pos = sp.GetTargetPosition(self.hc, 0, sp.SYNCHRONOUS)
        y_pos = sp.GetTargetPosition(self.hc, 1, sp.SYNCHRONOUS)
        return x_pos, y_pos

    def move_stage_to_point(self, x, y, velocity=20, endVelocity=0):
        sp.ExtToPointM(
            self.hc,
            sp.MotionFlags.ACSC_AMF_VELOCITY | sp.MotionFlags.ACSC_AMF_ENDVELOCITY,
            [0,1,-1],
            point=[x,y],
            velocity=velocity,
            endVelocity= 0,
            failure_check=True
        )

class HexapodController:
    def __init__(self, hexapod_port, hexapod_baud=115200):
        self.hp = pipython.GCS2Device('C-887')
        try:
            self.hp.ConnectRS232(hexapod_port, hexapod_baud)
            self.connected = True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.connected = False

    def zero_hexapod(self):
        if not self.connected:
            raise RuntimeError("Hexapod not connected.")
        axes = ['X', 'Y', 'Z', 'U', 'V', 'W']
        for axis in axes:
            self.hp.MOV(axis, 0)

    def close(self):
        if self.connected:
            try:
                self.hp.CloseConnection()
                self.connected = False
            except Exception as e:
                print(f"Error closing hexapod: {e}")

    def get_hexapod_pos(self):
        return self.hp.qPOS(['X', 'Y', 'Z', 'U', 'V', 'W'])

    def move_hexapod(self, positions):
        for pos in positions:
            self.hp.MOV(pos, positions[pos])
