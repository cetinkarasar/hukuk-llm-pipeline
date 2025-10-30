"https://huggingface.co/Cetin003/hukuk_model_tck_v1_lora" adresinden fine tune ettiğim modeli colabda çalıştırıp test edebilirsiniz colabda
Bu model bir LoRA adaptörüdür ve unsloth ile eğitilmiştir
Aşağıdaki hücreleri sırayla yeni bir Colab defterine yapıştırıp çalıştırabilir:

!pip install "unsloth[colab-new]"
---------------------------------
from unsloth import FastLanguageModel
from transformers import AutoTokenizer
import torch
--------------------------------------------------------------

hf_repo_name = "Cetin003/hukuk_model_tck_v1_lora"


print(f"Model yükleniyor: {hf_repo_name}")


model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = hf_repo_name,
    load_in_4bit = True,
    dtype = None,
)

print("Model ve Tokenizer başarıyla yüklendi!")
----------------------------------------------------------------

print("\n--- Model Test Ediliyor ---")

# Modelin eğitildiği Alpaca formatı
alpaca_prompt = """Aşağıda, bir görevi açıklayan bir talimat (instruction) ile daha fazla bağlam sağlayan bir girdi (input) bulunmaktadır. İsteği uygun şekilde tamamlayan bir yanıt (output) yazın.

### Talimat:
{}

### Girdi:
{}

### Yanıt:
{}"""


instruction = "Bu kanun maddesini bir vatandaşa açıklıyormuş gibi daha basit bir dille anlat."
input_text = "(TCK Madde 204) (1) Bir resmî belgeyi sahte olarak düzenleyen, gerçek bir resmî belgeyi başkalarını aldatacak şekilde değiştiren veya sahte resmî belgeyi kullanan kişi, iki yıldan beş yıla kadar hapis cezası ile cezalandırılır."


prompt = alpaca_prompt.format(
    instruction,
    input_text,
    "" # Yanıt kısmı boş
)


inputs = tokenizer([prompt], return_tensors = "pt", padding = False, truncation = True).to("cuda")

outputs = model.generate(
    **inputs,
    max_new_tokens = 512,
    pad_token_id = tokenizer.eos_token_id,
    do_sample = True,
    temperature = 0.3,
    repetition_penalty = 1.15,
    top_p = 0.95,
    top_k = 40
)

decoded_output = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

print("\n--- Modelin Cevabı ---")

response_start_index = decoded_output.find("### Yanıt:")
if response_start_index != -1:
    response = decoded_output[response_start_index + len("### Yanıt:"):]
    print(response.strip())
else:
    print("Model '### Yanıt:' etiketini üretmedi, tam çıktıyı gösteriyorum:")
    print(decoded_output)

