
class RLAgent:
    """Placeholder RL/ML interface.
    """
    def __init__(self, model_path=None, enabled=False):
        self.model_path = model_path
        self.enabled = enabled
        self.model = None

    def load_model(self, path):
        #Placeholder for loading a trained model(YES WE ARE THAT LAZY)
        self.model_path = path
        self.model = None

    def select_action(self, observation):
        #This is a stub (This was needed to do an action after an observation does nothing rn bc no model loaded)
        return None

    def observe(self, observation, reward, done):
        #Hook for online training/logging
        pass

    def train_async(self):
        #Background training loop (Not coded as of rn)
        pass
