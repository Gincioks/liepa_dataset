import pandas as pd
from datasets import Dataset, Audio

tsv_path = "liepa_dataset/train.tsv" # define the path to your TSV file containing the audio data
clips_path = "liepa_dataset/clips" # define the path to your audio files

df = pd.read_csv(tsv_path, sep="\t") # read the TSV file using pandas

common_voice_dataset = Dataset.from_pandas(df).cast_column("audio", Audio()) # # use datasets library to create the audio dataset

common_voice_dataset.push_to_hub("gincioks/liepa_sentences", private=True)



