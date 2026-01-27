import base64
from openai import OpenAI
try:
    from experiments.cost_calculator import ImageAnalysisCostCalculator
except ImportError:
    from cost_calculator import ImageAnalysisCostCalculator  # when run from experiments/

client = OpenAI()

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Path to your image
image_path = "images/IMG_7712.JPG"

# Read prompt from file
prompt_path = "backend/prompts/handwriting_ocr.txt"
with open(prompt_path, "r", encoding="utf-8") as prompt_file:
    prompt_text = prompt_file.read().strip()

# Calculate cost before making the API call
cost_calculator = ImageAnalysisCostCalculator(model="gpt-4.1", tier="standard")
cost_info = cost_calculator.calculate_cost_both(image_path=image_path, detail="high")
print(f"Estimated cost for this image:")
print(f"  Tokens: {cost_info['tokens']:,}")
print(f"  Dollars: ${cost_info['dollars']:.6f}")
print(f"  Model: {cost_info['model']} ({cost_info['tier']} tier)")

# Getting the Base64 string
base64_image = encode_image(image_path)

response = client.responses.create(
    model="gpt-4.1",
    input=[
        {
            "role": "user",
            "content": [
                { "type": "input_text", "text": prompt_text },
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"
                },
            ],
        }
    ],
)

print(response.output_text)