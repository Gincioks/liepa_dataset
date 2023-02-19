import soundfile as sf
import pandas as pd
from datasets import Dataset, Audio
from sklearn.model_selection import train_test_split

# define the path to your TSV file containing the audio data
tsv_path = "train.tsv"

# define the path to your audio files
clips_path = "clips"

# read the TSV file using pandas
df = pd.read_csv(tsv_path, sep="\t")

# # use datasets library to create the audio dataset
common_voice_dataset = Dataset.from_pandas(df).cast_column("audio", Audio())

common_voice_dataset.push_to_hub("gincioks/liepa_sentences", private=True)



