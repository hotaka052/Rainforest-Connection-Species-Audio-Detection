import numpy as np
import librosa
import colorednoise as cn

class AudioTransform:
    def __init__(self, always_apply = False, p = 0.5):
        self.always_apply = always_apply
        self.p = p

    def __call__(self, y: np.ndarray):
        if self.always_apply:
            return self.apply(y)
        else:
            if np.random.rand() < self.p:
                return self.apply(y)
            else:
                return y

    def apply(self, y: np.ndarray):
        raise NotImplementedError

class Compose:
    def __init__(self, transforms:list):
        self.transforms = transforms
        
    def __call__(self, y:np.ndarray):
        for trns in self.transforms:
            y = trns(y)
            
        return y

class OneOf:
    def __init__(self, transforms:list):
        self.transforms = transforms
        
    def __call__(self, y:np.ndarray):
        n_trns = len(self.transforms)
        trns_idx = np.random.choice(n_trns)
        trns = self.transforms[trns_idx]
        
        return trns(y)

class GaussianNoiseSNR(AudioTransform):
    def __init__(self, always_apply = False, p = 0.5, min_snr = 5.0, max_snr = 20.0, **kwargs):
        super().__init__(always_apply, p)
        
        self.min_snr = min_snr
        self.max_snr = max_snr
        
    def apply(self, y:np.ndarray, **params):
        snr = np.random.uniform(self.min_snr, self.max_snr)
        a_signal = np.sqrt(y ** 2).max()
        a_noise = a_signal / (10 ** (snr / 20))
        
        white_noise = np.random.randn(len(y))
        a_white = np.sqrt(white_noise ** 2).max()
        augmented = (y + white_noise * 1 / a_white * a_noise).astype(y.dtype)
        
        return augmented

class PinkNoiseSNR(AudioTransform):
    def __init__(self, always_apply = False, p = 0.5, min_snr = 5.0, max_snr = 20.0, **kwargs):
        super().__init__(always_apply, p)
        
        self.min_snr = min_snr
        self.max_snr = max_snr
        
        
    def apply(self, y:np.ndarray, **params):
        snr = np.random.uniform(self.min_snr, self.max_snr)
        a_signal = np.sqrt(y ** 2).max()
        a_noise = a_signal / (10 ** (snr / 20))
                              
        pink_noise = cn.powerlaw_psd_gaussian(1, len(y))
        a_pink = np.sqrt(pink_noise ** 2).max()
        augmented = (y + pink_noise * 1 / a_pink * a_noise).astype(y.dtype)
        
        return augmented

class PitchShift(AudioTransform):
    def __init__(self, always_apply = False, p = 0.5, max_steps = 5, sr = 32000):
        super().__init__(always_apply, p)
        
        self.max_steps = max_steps
        self.sr = sr
        
    def apply(self, y:np.ndarray, **params):
        n_steps = np.random.randint(-self.max_steps, self.max_steps)
        augmented = librosa.effects.pitch_shift(y, sr = self.sr, n_steps = n_steps)
        
        return augmented

class TimeShift(AudioTransform):
    def __init__(self, always_apply = False, p = 0.5, max_shift_second = 2, sr = 32000, padding_mode = 'replace'):
        super().__init__(always_apply, p)
        
        assert padding_mode in ['replace', 'zero'], "`padding_mode` must be either 'replace' or 'zero'"
        self.max_shift_second = max_shift_second
        self.sr = sr
        self.padding_mode = padding_mode
        
    def apply(self, y:np.ndarray, **params):
        shift = np.random.randint(-self.sr * self.max_shift_second, self.sr * self.max_shift_second)
        augmented = np.roll(y, shift)
        if self.padding_mode == 'zero':
            if shift > 0:
                augmented[:shift] = 0
            else:
                augmented[shift:] = 0
        
        return augmented