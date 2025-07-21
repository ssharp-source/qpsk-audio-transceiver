import py_trees
import os
import time
from transmitter import transmit_file
from receiver import run_receiver

TRANSMIT_FOLDER = "./transmit"
RECEIVE_DURATION = 5  # seconds

# --- Behavior Nodes ---

class CheckTransmitFolder(py_trees.behaviour.Behaviour):
    def __init__(self):
        super().__init__("CheckTransmitFolder")

    def update(self):
        files = os.listdir(TRANSMIT_FOLDER)
        if files:
            self.blackboard = py_trees.blackboard.Blackboard()
            self.blackboard.tx_file = os.path.join(TRANSMIT_FOLDER, files[0])
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE

class CheckChannelFree(py_trees.behaviour.Behaviour):
    def __init__(self):
        super().__init__("CheckChannelFree")

    def update(self):
        print("Checking channel...")
        busy = run_receiver(duration_sec=1)
        if not busy:
            print("Channel is free.")
            return py_trees.common.Status.SUCCESS
        else:
            print("Channel busy.")
            return py_trees.common.Status.FAILURE

class TransmitFile(py_trees.behaviour.Behaviour):
    def __init__(self):
        super().__init__("TransmitFile")

    def update(self):
        bb = py_trees.blackboard.Blackboard()
        if hasattr(bb, "tx_file") and os.path.exists(bb.tx_file):
            print(f"Transmitting {bb.tx_file}")
            transmit_file(bb.tx_file)
            os.remove(bb.tx_file)  # Optional: delete after transmit
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE

class ReceiveAndWait(py_trees.behaviour.Behaviour):
    def __init__(self):
        super().__init__("ReceiveAndWait")

    def update(self):
        print("Running receiver...")
        run_receiver(duration_sec=RECEIVE_DURATION)
        return py_trees.common.Status.SUCCESS

# --- Main Loop ---

def create_behavior_tree():
    root = py_trees.composites.Selector("MainSelector")

    transmit_seq = py_trees.composites.Sequence("TransmitSequence")
    transmit_seq.add_children([
        CheckTransmitFolder(),
        CheckChannelFree(),
        TransmitFile()
    ])

    root.add_children([
        transmit_seq,
        ReceiveAndWait()
    ])

    return py_trees.trees.BehaviourTree(root)

if __name__ == "__main__":
    tree = create_behavior_tree()

    print("\n--- Radio Controller Starting ---\n")
    while True:
        tree.tick()
        time.sleep(0.5)
