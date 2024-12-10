# pip install 'fireworks-ai'
import fireworks.client
from fireworks.client.image import ImageInference, Answer

# Initialize the ImageInference client
fireworks.client.api_key = "$API_KEY"
inference_client = ImageInference(model="accounts/fullstackwebdev-9ec139/deployedModels/llama-v3p2-11b-vision-instruct-463869f8")

# Generate an image using the text_to_image method
answer : Answer = inference_client.text_to_image(
    prompt="A beautiful sunset over the ocean",
    cfg_scale=undefined,
    height=1024,
    width=1024,
    sampler=None,
    steps=undefined,
    seed=0,
    safety_check=False,
    output_image_format="JPG",
    # Add additional parameters here
)

if answer.image is None:
  raise RuntimeError(f"No return image, {answer.finish_reason}")
else:
  answer.image.save("output.jpg")