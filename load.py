from datasets import load_dataset, DatasetDict

# Variables
token = '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'
data_set_name = "mozilla-foundation/common_voice_11_0"
language = "Lithuanian"
language_code = "lt"
pre_trained_model = "openai/whisper-tiny"
output_dir = "./whisper-tiny-lt"
model_name = "whisper-tiny-lt"

# STEP 1. Download Dataset
common_voice = DatasetDict()

# common_voice["train"] = load_dataset(data_set_name, language_code, split="train+validation", use_auth_token=True)
liepa_sentences = load_dataset("gincioks/liepa_sentences", split="train", use_auth_token=True)
common_voice["train"] = load_dataset(data_set_name, language_code, use_auth_token=True)
common_voice["test"] = load_dataset(data_set_name, language_code, split="test", use_auth_token=True)

print(liepa_sentences)

# common_voice = common_voice.remove_columns(
#     ["accent",
#      "age",
#      "client_id",
#      "down_votes",
#      "gender",
#      "locale",
#      "path",
#      "segment",
#      "up_votes"]
#     )

# print(common_voice)