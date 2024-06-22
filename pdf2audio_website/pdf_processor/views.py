from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from pdfminer.high_level import extract_text
from google.generativeai import configure as genai_configure
from google.generativeai import GenerativeModel
from google.cloud import texttospeech
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Set Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/pokeydex/Projects/pdf2audio_website/credentials_key.json"

def process_pdf(request):
    if request.method == 'POST' and request.FILES['pdf_file']:
        pdf_file = request.FILES['pdf_file']
        
        # Ensure the media directory exists
        media_directory = settings.MEDIA_ROOT
        if not os.path.exists(media_directory):
            os.makedirs(media_directory)
        
        # Save uploaded PDF file to media directory
        pdf_path = os.path.join(media_directory, pdf_file.name)
        with open(pdf_path, 'wb') as f:
            for chunk in pdf_file.chunks():
                f.write(chunk)
        
        # Extract text from PDF
        text = extract_text(pdf_path)
        
        # Configure Generative AI API
        genai_configure(api_key=API_KEY)
        model = GenerativeModel('gemini-1.5-flash')
        
        # Format the text using Generative AI
        response = model.generate_content(
            "In the Following text remove all the numbers and special characters, make it more readable and give the response in paragraphs, don't give it in points only in paragraphs. Here is text: \n" + text)
        
        formatted_text = response.text
        
        # Initialize Text-to-Speech client
        client = texttospeech.TextToSpeechClient()
        
        # Prepare input for text-to-speech synthesis
        synthesis_input = texttospeech.SynthesisInput(text=formatted_text)
        
        # Define voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        
        # Define audio output configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Synthesize speech and write to file with PDF name
        output_file = os.path.splitext(pdf_file.name)[0] + ".mp3"
        output_path = os.path.join(settings.MEDIA_ROOT, output_file)
        
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        # Write audio content to file
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        
        # Return a response with a link to download the generated audio
        audio_url = os.path.join(settings.MEDIA_URL, output_file)
        return HttpResponse(f'Audio generated successfully! <a href="{audio_url}">Download Audio</a>')
    
    return render(request, 'pdf_processor/index.html')
