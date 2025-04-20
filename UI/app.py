from flask import Flask, render_template
import re
import os
import requests
from flask import Flask, render_template, request, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, white
from PIL import Image
from io import BytesIO
import os
import openai
from dotenv import load_dotenv
load_dotenv()

HF_TOKEN = os.getenv("HF_API_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")


app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("home.html")

def build_prompt(premise):
    return f"""Below are examples of anime short stories, each structured into exactly 5 manga panels:

---

Title: The Last Samurai
Characters: Ryu, Hana, Master Kaito
Panel 1: Ryu trains fiercely under Master Kaito's watchful eyes at dawn.
Panel 2: Hana secretly watches Ryu from behind a cherry blossom tree, smiling gently.
Panel 3: Enemy samurai burst into the dojo; Master Kaito steps forward confidently.
Panel 4: Ryu and Hana fight side-by-side against the attackers, swords clashing dramatically.
Panel 5: With enemies defeated, Ryu and Hana exchange quiet glances beneath falling cherry blossoms.

---

Title: The Spirit Painter
Characters: Mei, Old Master Kuro
Panel 1: Mei enters a forgotten temple, sketchbook in hand, led by whispers of a legendary painter.
Panel 2: She finds a crumbling mural with faded colors that seem to shift when she draws near.
Panel 3: As she sketches, a phantom hand begins painting beside her, matching her every stroke.
Panel 4: The mural comes to life, revealing Old Master Kuro, whose spirit had waited for centuries.
Panel 5: The two artists nod in understanding before he fades, leaving Mei’s sketchbook glowing softly.

Title: The Clockmaker's Promise
Characters: Aiko, Grandpa Renji

Panel 1: Aiko dusts off an old grandfather clock in her grandfather’s quiet workshop.
Panel 2: She accidentally winds it, and gears begin to spin with a golden glow.
Panel 3: A vision of her younger grandfather appears, tinkering joyfully beside her.
Panel 4: Aiko smiles through tears as they work together in sync, fixing the broken timepiece.
Panel 5: The clock chimes once more, the vision fades, and Aiko bows gratefully to the silent room.

---

Now create another short anime story structured into exactly 5 manga panels based on this premise:

**Premise:** {premise}

Title:"""

def clean_story(generated_text: str):
    match = re.search(r"(Panel 5:.*?)(\n|$)", generated_text, flags=re.DOTALL)
    if match:
        return generated_text[:match.end()].strip()
    return generated_text.strip()

def generate_story_from_premise(premise: str):
    prompt = build_prompt(premise)

    HF_API_URL = "https://nvigrln2dsmvudvh.us-east-1.aws.endpoints.huggingface.cloud"
    HF_TOKEN = os.getenv("HF_API_TOKEN_LLAMA")  # Secure approach, or hardcode for now

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.8,
            "top_p": 0.95,
            "repetition_penalty": 1.1,
            "do_sample": True
        }
    }

    response = requests.post(HF_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        generated_text = result
        story = generated_text[len(prompt):].strip()
        return clean_story(story)

    else:
        print("❌ Error from HF API:", response.status_code, response.text)
        return "Error: Could not generate story"

def parse_story_to_panels(story_text):
    panel_lines = re.findall(r"(Panel\s*\d:\s*.*)", story_text)
    panel_dict = {}
    characters = []

    for i, line in enumerate(panel_lines):
        panel_num = f"panel_{i+1}"
        panel_text = line.split(":", 1)[-1].strip()
        panel_dict[panel_num] = panel_text

    match = re.search(r"Character[s]?:\s*(.*)", story_text)
    if match:
        characters = [name.strip() for name in match.group(1).split(",")]
    characters = ", ".join(characters)

    return panel_dict, characters

def build_subpanel_prompt(panel_summary, characters):
    return f"""You are a skilled manga storyboard artist. Given a single-sentence manga panel summary, expand it into 3–4 detailed **subpanels**. Each subpanel should describe a distinct visual beat using camera angle, emotion, posture, or background. Focus on visual storytelling. Do not include dialogue or narration.

---

Example 1:

Scene: A teenager waits alone in the kitchen as the rain pours outside.

Subpanel 1: Wide shot of a quiet kitchen, shadows stretching across the tiled floor.  
Subpanel 2: Medium shot from the side, showing the teen sitting at the table, resting their chin on their hand.  
Subpanel 3: Close-up of raindrops trailing down the window behind them.  
Subpanel 4: A low angle shows their hand slowly tapping against a cold cup of tea.

---

Example 2:

Scene: A child finds a cracked photo frame buried in a dusty drawer.

Subpanel 1: Close-up of the child’s hand brushing away dust from an old drawer.  
Subpanel 2: Overhead shot revealing the cracked frame peeking out beneath scattered trinkets.  
Subpanel 3: A focused shot of the child’s surprised expression as they lift the frame.  
Subpanel 4: Dramatic angle from behind the child as light from the window highlights the photo’s worn image.

---

Now generate 3–4 subpanels for the following:

Scene: {panel_summary}  
Characters: {characters}
"""


def elaborate_panel(panel_summary, characters):
    prompt = build_subpanel_prompt(panel_summary, characters)
    SUBPANEL_API_URL = "https://awtq5ci791oibd2p.us-east-1.aws.endpoints.huggingface.cloud/"  # Replace this with the real one
    HF_TOKEN =  os.getenv("HF_API_TOKEN_MISTRAL")  # Or hardcode if needed for testing

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 160,
            "temperature": 0.85,
            "top_p": 0.95,
            "repetition_penalty": 1.2,
            "do_sample": False
        }
    }

    response = requests.post(SUBPANEL_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        # You may need to adjust this depending on response format
        generated_text = result[0]["generated_text"]
        subpanels_only = generated_text[len(prompt):].strip()
        return subpanels_only
    else:
        print("❌ Subpanel API error:", response.status_code, response.text)
        return "Error: Subpanel generation failed"

def build_dalle_prompt(panel_number, story_title, character_names, subpanel_description):
    return f"""You are illustrating panel {panel_number} of a black-and-white manga titled '{story_title}'.

Scene Description:
{subpanel_description}

Characters featured: {', '.join(character_names)}

Visual Requirements:
- Use a consistent manga illustration style across all panels.
- Maintain character design coherence (hairstyle, outfit, posture, emotion).
- Reflect the emotional tone and visual storytelling in the scene.
- Include background environment as described (lighting, mood, location).
- Do NOT include speech bubbles or text.
- Draw as if this panel follows directly after the previous one in a printed manga.

Output a black-and-white panel suitable for a storybook or comic sequence."""

def extract_title_and_characters(story_text):
    lines = story_text.strip().splitlines()
    title = lines[0].strip()
    characters_line = next((line for line in lines if line.lower().startswith("characters:")), "")
    characters = [c.strip() for c in characters_line.split(":", 1)[-1].split(",")] if characters_line else []
    return title, characters


def save_images_to_pdf(image_data_dict, output_path="manga_story.pdf"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    padding = 40
    image_width = width - 2 * padding
    text_height = 60
    box_height = 30

    # ADD COVER PAGE
    story_title = os.path.basename(output_path).replace(".pdf", "").replace("_", " ")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height / 2 + 20, story_title)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height / 2 - 10, "A manga-style short story")
    c.showPage()

    # Begin actual image pages
    for key in sorted(image_data_dict.keys()):
        img_url, narration = image_data_dict[key]

        # Download image
        response = requests.get(img_url)
        img = Image.open(BytesIO(response.content))

        # Force grayscale for manga look
        img = img.convert("L").convert("RGB")

        # Resize and save temporary image
        img = img.resize((int(image_width), int(image_width)))
        temp_img_path = f"temp_{key}.jpg"
        img.save(temp_img_path)

        # Draw image
        c.drawImage(temp_img_path, padding, text_height + box_height + 10, width=image_width, preserveAspectRatio=True)

        # Draw black narration box
        c.setFillColor(black)
        c.rect(padding - 5, text_height - 10, image_width + 10, box_height, fill=1, stroke=0)

        # Write narration
        c.setFont("Helvetica", 12)
        c.setFillColor(white)
        c.drawString(padding, text_height + 5, narration)

        c.showPage()
        os.remove(temp_img_path)

    c.save()
    print(f" PDF saved to: {output_path}")



@app.route("/generate", methods=["POST"])
def generate():
    detailed_panels = {}
    data = request.get_json()
    premise = data.get("prompt", "")

    story = generate_story_from_premise(premise)
    panel_dict, characters = parse_story_to_panels(story)

    for key, panel_summary in panel_dict.items():
        detailed_output = elaborate_panel(panel_summary, characters)
        detailed_panels[key] = detailed_output

    openai.api_key =  os.getenv("OPENAI_API_KEY")
    panel_images = {}
    story_title, characters = extract_title_and_characters(story)
    pdf_filename = f"{story_title.replace(' ', '_')}.pdf"
    for i in range(1, 6):
        panel_key = f"panel_{i}"
        panel_desc = detailed_panels[panel_key]
        narration = panel_dict[panel_key]

        dalle_prompt = build_dalle_prompt(i, story_title, characters, panel_desc)

        print(f"\n Generating image for {panel_key}...\nPrompt:\n{dalle_prompt}\n")

        try:
            response = openai.Image.create(
                model="dall-e-3",
                prompt=dalle_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = response["data"][0]["url"]
            panel_images[panel_key] = (image_url, narration)
            print(f" Generated Image URL for {panel_key}: {image_url}\n{'='*60}")
        except Exception as e:
            print(f" Failed to generate {panel_key}: {str(e)}")

    output_path = os.path.join("static", "generated", pdf_filename)
    save_images_to_pdf(panel_images, output_path=output_path)
    

    safe_title = story_title.replace(" ", "_")
    return jsonify({
    "status": "done",
    "title": story_title,
    "pdf_path": f"/static/generated/{safe_title}.pdf"
})

  # Can return nothing if you prefer




if __name__ == "__main__":
    app.run(debug=True)

