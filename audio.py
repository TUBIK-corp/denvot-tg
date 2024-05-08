from audio_separator.separator import Separator
import time

class AudioSeparator:
    def __init__(self,
                 output_dir='output',
                 log_level='WARNING',
                 denoise_enabled=True,
                 normalization_enabled=False,
                 model_file_dir='models',
                 model_name='UVR_MDXNET_KARA_2',
                 segment_size=256,
                 hop_length=1024,
                 log_formatter='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
        self.separator = Separator(model_file_dir=model_file_dir,
                                   segment_size=segment_size,
                                   hop_length=hop_length,
                                   output_dir=output_dir,
                                   log_level=log_level,
                                   denoise_enabled=denoise_enabled,
                                   normalization_enabled=normalization_enabled,
                                   log_formatter=log_formatter)
        self.separator.load_model(model_name)
        print("Loaded model:", model_name)

    def __call__(self, audio_path):
        return self.separate(audio_path)

    def separate(self, audio_path):
        print('Separating', audio_path)
        start_time = time.time()
        primary_stem_path, secondary_stem_path = self.separator.separate(audio_path)
        end_time = time.time()
        print(f'Separation took {end_time - start_time:.2f} seconds')
        return primary_stem_path, secondary_stem_path


if __name__ == '__main__':
    separate = AudioSeparator()
    print(separate('DenVot - Propaganda.mp3'))