from silero_vad import load_silero_vad, get_speech_timestamps
import torch

# Load pre-trained VAD model (lightweight, runs on CPU)
model = load_silero_vad()

def is_speech(audio, sample_rate=16000):
    """
    Detect if given audio chunk contains speech

    Parameters:
    - audio: numpy array (float32 waveform)
    - sample_rate: must be 16000 for Silero

    Returns:
    - True if speech detected
    - False otherwise
    """

    # Convert to torch tensor (required by model)
    audio_tensor = torch.tensor(audio)

    # Get speech segments
    timestamps = get_speech_timestamps(
        audio_tensor,
        model,
        sampling_rate=sample_rate
    )

    # If any speech segment detected → return True
    return len(timestamps) > 0