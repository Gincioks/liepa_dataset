from transformers import Trainer, TrainingArguments, AutoConfig, WhisperForConditionalGeneration, PushToHubMixin
from huggingface_hub import HfApi, HfFolder

model_name = "whisper-tiny-lt"
model_dir = f"./{model_name}"
language = "Lithuanian"
token = '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'
data_set_name = "mozilla-foundation/common_voice_11_0"
language = "Lithuanian"
language_code = "lt"
pre_trained_model = "openai/whisper-tiny"

def login_hugging_face(token: str) -> None:
    """
    Loging to Hugging Face portal with a given token.
    """
    api = HfApi()
    api.set_access_token(token)
    folder = HfFolder()
    folder.save_token(token)

    return None

login_hugging_face(token)
print('We are logged in to Hugging Face now!')

# Load the configuration, tokenizer, and model
config = AutoConfig.from_pretrained(model_dir)

model = WhisperForConditionalGeneration.from_pretrained(model_dir, config=config)

# Load all checkpoints for the model
trainer = Trainer(
    model=model,
    args=TrainingArguments(output_dir=model_dir, disable_tqdm=True),
    train_dataset=None,
    data_collator=None,
)
checkpoints = trainer.checkpoints

# Find the best checkpoint
best_checkpoint = trainer.find_best_checkpoint(metric="eval_loss")

# Upload the best checkpoint to the Hugging Face Hub

class MyModel(WhisperForConditionalGeneration, PushToHubMixin):
    pass

model = MyModel.from_pretrained(best_checkpoint)
kwargs = {
    "dataset_tags": data_set_name,
    "dataset": "Common Voice 11.0",  # a 'pretty' name for the training dataset
    "dataset_args": "config: lt, split: test",
    "language": language_code,
    "model_name": model_name,  # a 'pretty' name for our model
    "finetuned_from": pre_trained_model,
    "tasks": "automatic-speech-recognition",
    "tags": "hf-asr-leaderboard",
}
model.push_to_hub(model_name, **kwargs)