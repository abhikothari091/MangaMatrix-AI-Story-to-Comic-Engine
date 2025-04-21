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
from PIL import Image, ImageDraw, ImageFont
import textwrap
import img2pdf
from fpdf import FPDF


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
    

def generate_speech_bubble_text(narration, panel_desc, characters):
    """
    Generates dialogue for the characters based on the narration and panel description.
    
    Args:
        narration (str): The narration text.
        panel_desc (str): The panel description.
        characters (list): List of character names in the panel.
    
    Returns:
        str: Dialogue in the format "Character: Speech\nCharacter2: Speech2\n..."
    """
    prompt = (
        f"You are a manga scriptwriter creating dialogue for a comic panel in a fantasy manga.\n"
        f"**Scene Context:** This panel takes place in a traditional Japanese setting with a magical twist. "
        f"The main character, a young girl named Mika, is on a quest to return magical cards containing forgotten dreams. "
        f"She is cheerful and determined. Other characters may include her classmates, family, or ancestral spirits.\n"
        f"**Narration:** {narration}\n"
        f"**Panel Description:** {panel_desc}\n"
        f"**Characters in Panel:** {', '.join(characters)}\n\n"
        f"Generate short, natural, and context-appropriate dialogue for the characters in this panel. "
        f"Each line must be prefixed with the character's name (e.g., 'Mika: \"Speech\"'). "
        f"Do not include narration, descriptions, or explanations—only the dialogue. "
        f"Ensure the dialogue fits a manga style, with concise and expressive lines that reflect the characters' personalities.\n\n"
        f"Example:\n"
        f"Mika: \"Wow, this place is amazing!\"\n"
        f"Yuki: \"Mika, look! The mural is glowing!\"\n"
        f"Mrs. Yamada: \"These are your ancestors, child.\""
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=100,
            top_p=0.85
        )
        
        dialogue = response['choices'][0]['message']['content'].strip()
        
        if not dialogue or len(dialogue.split("\n")) < 1:
            raise ValueError("Generated dialogue is empty or invalid.")
        
        if not any(c.isalpha() for c in dialogue) or len(dialogue) < 5:
            raise ValueError("Generated dialogue appears to be gibberish.")
        
        lines = dialogue.split("\n")
        valid_lines = [line for line in lines if ":" in line and len(line.split(":")) == 2]
        dialogue = "\n".join(valid_lines)
        
        return dialogue
    
    except Exception as e:
        print(f"Error generating dialogue: {str(e)}")
        return "\n".join([f"{char}: \"...\"" for char in characters])

def build_dalle_prompt(panel_number, story_title, character_names, subpanel_description, dialogue, narration):
    """
    Builds a prompt for DALL·E to generate a manga panel with pre-generated dialogue and narration.
    
    Args:
        panel_number (int): The panel number.
        story_title (str): The title of the story.
        character_names (list): List of character names.
        subpanel_description (str): The subpanel description.
        dialogue (str): Pre-generated dialogue for the panel.
        narration (str): Narration text to place at the bottom.
    
    Returns:
        str: The prompt for DALL·E.
    """
    # Format the dialogue for inclusion in the prompt
    dialogue_text = dialogue.strip().replace("\n", " | ")
    
    return f"""You are illustrating panel {panel_number} of a manga titled '{story_title}'.

Scene Description:
{subpanel_description}

Characters featured: {', '.join(character_names)}

Dialogue to include in speech bubbles (format: Character: Speech | Character2: Speech2):
{dialogue_text}

Narration to include at the bottom of the panel (not in a speech bubble, spanning the full width):
{narration}

Visual Requirements:
- Draw images in full color, vibrant, detailed background in colorful manga/anime style. Use rich and vivid colors.
- Use a consistent manga illustration style across all panels.
- Maintain character design coherence (hairstyle, outfit, posture, emotion).
- Reflect the emotional tone and visual storytelling in the scene.
- Include background environment as described (lighting, mood, location).
- Have dynamic speech bubble placement for the dialogue, ensuring bubbles do not cover characters' faces.
- Place the narration text at the bottom of the panel in a rectangular box, spanning the full width, without overlapping the main image content.
- Draw as if this panel follows directly after the previous one in a printed manga.

Output a colored panel suitable for a storybook or comic sequence."""



def build_dalle_prompt(panel_number, story_title, character_names, subpanel_description, dialogue, narration):
    """
    Builds a prompt for DALL·E to generate a manga panel with pre-generated dialogue and narration.
    
    Args:
        panel_number (int): The panel number.
        story_title (str): The title of the story.
        character_names (list): List of character names.
        subpanel_description (str): The subpanel description.
        dialogue (str): Pre-generated dialogue for the panel.
        narration (str): Narration text to place at the bottom.
    
    Returns:
        str: The prompt for DALL·E.
    """
    # Format the dialogue for inclusion in the prompt
    dialogue_text = dialogue.strip().replace("\n", " | ")
    
    return f"""You are illustrating panel {panel_number} of a manga titled '{story_title}'.

Scene Description:
{subpanel_description}

Characters featured: {', '.join(character_names)}

Dialogue to include in speech bubbles (format: Character: Speech | Character2: Speech2):
{dialogue_text}

Narration to include at the bottom of the panel (not in a speech bubble, spanning the full width):
{narration}

Visual Requirements:
- Draw images in full color, vibrant, detailed background in colorful manga/anime style. Use rich and vivid colors.
- Use a consistent manga illustration style across all panels.
- Maintain character design coherence (hairstyle, outfit, posture, emotion).
- Reflect the emotional tone and visual storytelling in the scene.
- Include background environment as described (lighting, mood, location).
- Have dynamic speech bubble placement for the dialogue, ensuring bubbles do not cover characters' faces.
- Place the narration text at the bottom of the panel in a rectangular box, spanning the full width, without overlapping the main image content.
- Draw as if this panel follows directly after the previous one in a printed manga.

Output a colored panel suitable for a storybook or comic sequence."""


def build_cover_page_prompt(story_title, characters, premise):
    return f"""You are a professional manga cover artist. Your task is to illustrate the front cover for a manga titled **'{story_title}'**.

Scene Description:
Create a vibrant, full-color manga-style cover showcasing the main characters: {', '.join(characters)}. Capture their personality and relationships in a single powerful frame.

Premise:
"{premise}"

Visual Requirements:
- Full-color, vibrant, highly detailed anime/manga style with dramatic lighting and shading.
- Character consistency: For example, Mika should have a cheerful expression, short hair, and wear a school uniform.
- Place characters in dynamic or expressive poses that reflect their roles in the story.
- Use a dynamic composition: Characters in the foreground, with a rich background that complements the theme (e.g., magical cityscape, school rooftop, train station, etc.).
- Leave space at the top or center for the manga title to be added later.
- Emphasize the emotional tone: mix of adventure, magic, and anticipation.
- This should resemble a professional printed manga volume cover — eye-catching and story-driven.
"""



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

def save_panels_to_pdf(panel_images, output_path="manga_story.pdf"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Ensure directory exists

    pdf = FPDF(unit="pt", format=[1024, 1024])
    for panel_key in sorted(panel_images.keys(), key=lambda k: int(k.split("_")[1])):
        image_path = panel_images[panel_key]["image_path"]
        pdf.add_page()
        pdf.image(image_path, 0, 0, 1024, 1024)

    pdf.output(output_path, "F")
    print(f"📘 PDF saved as {output_path}")

# def save_panels_to_pdf(panel_images, output_path="manga_story.pdf"):
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)

#     pdf = FPDF(unit="pt", format=[1024, 1024])

#     for panel_key in sorted(panel_images.keys()):
#         image_data = panel_images[panel_key]
#         image_path_or_url = image_data[0]

#         # Check if this is a URL or a file path
#         if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
#             response = requests.get(image_path_or_url)
#             image = Image.open(BytesIO(response.content)).convert("RGB")
#             temp_path = f"temp_{panel_key}.jpg"
#             image.save(temp_path, format="JPEG")
#             pdf.add_page()
#             pdf.image(temp_path, 0, 0, 1024, 1024)
#             os.remove(temp_path)
#         else:
#             # Local file
#             pdf.add_page()
#             pdf.image(image_path_or_url, 0, 0, 1024, 1024)

#     pdf.output(output_path, "F")
#     print(f"📘 PDF saved as {output_path}")


output_dir = os.path.join("static", "images")
@app.route("/generate", methods=["POST"])
def generate():
    print("🚀 /generate route called")
    detailed_panels = {}
    data = request.get_json()
    premise = data.get("prompt", "")

    story = generate_story_from_premise(premise)
    panel_dict, characters = parse_story_to_panels(story)

    for key, panel_summary in panel_dict.items():
        detailed_output = elaborate_panel(panel_summary, characters)
        detailed_panels[key] = detailed_output

    
    dialogues = {}
    for key, panel_summary in panel_dict.items():
        print(f"Generating dialogue for {key}:")
        narration = panel_summary  # Use panel summary as narration
        characters_list = characters  # Use the characters list directly
        dialogue = generate_speech_bubble_text(narration, panel_summary, characters_list)
        dialogues[key] = dialogue
        print(f"Dialogue for {key}:\n{dialogue}\n{'='*60}")

    openai.api_key =  os.getenv("OPENAI_API_KEY")
    panel_images = {}

    # Define font settings
    FONT_PATH = os.path.join("static", "fonts", "animeace.ttf")
    # FONT_PATH = "animeace.ttf"
    FALLBACK_FONT_PATH = "cc-wild-words-roman.ttf"
    FONT_SIZE = 20  # For narration
    TITLE_FONT_SIZE = 35  # For cover page title

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        title_font = ImageFont.truetype(FONT_PATH, TITLE_FONT_SIZE)
        print(f"Successfully loaded font: {FONT_PATH}")
    except:
        try:
            font = ImageFont.truetype(FALLBACK_FONT_PATH, FONT_SIZE)
            title_font = ImageFont.truetype(FALLBACK_FONT_PATH, TITLE_FONT_SIZE)
            print(f"Fallback to font: {FALLBACK_FONT_PATH}")
        except:
            try:
                font = ImageFont.truetype("arial.ttf", FONT_SIZE)
                title_font = ImageFont.truetype("arial.ttf", TITLE_FONT_SIZE)
                print("Fallback to system font: arial.ttf")
            except:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
                print("Fallback to PIL default font")

    # Define text and box styling
    TEXT_COLOR = "white"
    BOX_COLOR = (0, 0, 0, 180)  # Black with 70% opacity (RGBA)
    BOX_HEIGHT = 120  # For narration
    PADDING = 15
    BORDER_COLOR = (255, 255, 255, 255)  # White border
    TITLE_BOX_COLOR = (0, 0, 0, 200)  # Slightly darker for title



    story_title, characters_list = extract_title_and_characters(story)
    characters = [char.strip() for char in characters_list]
    pdf_filename = f"{story_title.replace(' ', '_')}.pdf"

    print("\nGenerating cover page...")
    cover_prompt = build_cover_page_prompt(story_title, characters, premise)
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=cover_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        image_url = response["data"][0]["url"]
        print(f"Generated Cover Page URL: {image_url}")

        # Fetch the image
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        # Open image
        image = Image.open(BytesIO(image_response.content)).convert("RGBA")
        width, height = image.size

        # Create a draw object
        draw = ImageDraw.Draw(image)

        # Add title text
        title_text = story_title.upper()  # Uppercase for impact
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Draw semi-transparent title box at the top
        title_box_height = text_height + 2 * PADDING
        draw.rectangle(
            [(0, 0), (width, title_box_height)],
            fill=TITLE_BOX_COLOR
        )
        draw.rectangle(
            [(0, 0), (width, title_box_height)],
            outline=BORDER_COLOR,
            width=2
        )

        # Draw title text
        x_text = (width - text_width) / 2
        y_text = PADDING
        draw.text((x_text, y_text), title_text, font=title_font, fill=TEXT_COLOR)

        # Save cover page
        cover_filename = os.path.join(output_dir, "cover_page.png")
        image.save(cover_filename, format="PNG")
        # panel_images["cover"] = {"image_path": cover_filename, "description": "Cover Page"}
        # panel_images["cover"] = (image_url, "Cover Page")
        panel_images["panel_0"] = {"image_path": cover_filename, "description": "Cover Page"}
        print(f"Saved {cover_filename}\n{'='*60}")

    except Exception as e:
        print(f"Failed to generate cover page: {str(e)}")
  



    for i in range(1, 6):
        panel_key = f"panel_{i}"
        panel_desc = panel_dict[panel_key]
        narration = panel_desc
        dialogue = dialogues[panel_key]
        detailed_desc = detailed_panels.get(panel_key, panel_desc)

        dalle_prompt = build_dalle_prompt(i, story_title, characters, detailed_desc, dialogue, narration)
        print(f"\nGenerating image for {panel_key}...\nPrompt:\n{dalle_prompt}\n")

        try:
            response = openai.Image.create(
                model="dall-e-3",
                prompt=dalle_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = response["data"][0]["url"]
            print(f"Generated Image URL for {panel_key}: {image_url}\n{'='*60}")

            image_response = requests.get(image_url)
            image_response.raise_for_status()

            image = Image.open(BytesIO(image_response.content)).convert("RGBA")
            width, height = image.size
            draw = ImageDraw.Draw(image)

            max_text_width = width - 2 * PADDING
            wrapped_text = []
            current_line = ""
            words = narration.split()

            for word in words:
                test_line = f"{current_line} {word}".strip()
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
                if text_width <= max_text_width:
                    current_line = test_line
                else:
                    wrapped_text.append(current_line)
                    current_line = word
            wrapped_text.append(current_line)

            line_height = draw.textbbox((0, 0), "Sample", font=font)[3] - draw.textbbox((0, 0), "Sample", font=font)[1]
            total_text_height = len(wrapped_text) * line_height + 2 * PADDING
            box_height = max(BOX_HEIGHT, total_text_height + PADDING)

            draw.rectangle(
                [(0, height - box_height), (width, height)],
                fill=BOX_COLOR
            )
            draw.rectangle(
                [(0, height - box_height), (width, height)],
                outline=BORDER_COLOR,
                width=2
            )

            y_text = height - box_height + PADDING
            for line in wrapped_text:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x_text = (width - text_width) / 2
                draw.text((x_text, y_text), line, font=font, fill=TEXT_COLOR)
                y_text += line_height

           
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, f"{panel_key}_with_narration.png")

            image.save(output_filename, format="PNG")

            panel_images[panel_key] = {
                "image_path": output_filename,
                "description": panel_desc
            }

            # panel_images[panel_key] = (image_url, narration)
            print(f"Saved {output_filename}\n{'='*60}")

        except Exception as e:
            print(f"Failed to generate {panel_key}: {str(e)}")



    output_path = os.path.join("static", "generated", pdf_filename)
    save_panels_to_pdf(panel_images, output_path=output_path)
    

    safe_title = story_title.replace(" ", "_")
    return jsonify({
    "status": "done",
    "title": story_title,
    "pdf_path": f"/static/generated/{safe_title}.pdf"
})

  # Can return nothing if you prefer




if __name__ == "__main__":
    app.run(debug=True)

