#!/usr/bin/env python3
import click
import os
import tempfile
from pathlib import Path
from .downloader import download_audio
from .transcriber import transcribe_audio
from .formatter import format_output
from .cleaner import clean_long_transcript

def process_video(url, output_dir, output_format, model, language, keep_audio, clean, llm_model, cleaning_style, save_raw):
    """Downloads, transcribes, and processes a single YouTube video."""
    try:
        click.echo(f"🎥 Downloading audio from: {url}")

        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path, video_title = download_audio(url, temp_dir)
            
            output_filename = f"{video_title}.{output_format}"
            output_path = Path(output_dir) / output_filename
            
            click.echo(f"🎙️  Transcribing '{video_title}' with {model} model...")
            
            result = transcribe_audio(audio_path, model, language)
            
            if save_raw or clean:
                raw_output_path = output_path.with_name(f"{video_title}_raw.{output_format}")
                
                if save_raw or not clean:
                    raw_formatted = format_output(result, output_format)
                    with open(raw_output_path, 'w', encoding='utf-8') as f:
                        f.write(raw_formatted)
                    
                    if save_raw:
                        click.echo(f"📄 Raw transcript saved to: {raw_output_path}")

            final_result = result
            if clean:
                click.echo(f"🧹 Cleaning transcript with {llm_model}...")
                raw_text = result['text']
                cleaned_text = clean_long_transcript(raw_text, llm_model, cleaning_style)
                
                if cleaned_text:
                    final_result = result.copy()
                    final_result['text'] = cleaned_text
                    if output_format in ['srt', 'vtt'] and 'segments' in result:
                        click.echo("ℹ️  Note: Cleaned text with original timing segments")
                else:
                    click.echo("⚠️  Cleaning failed, using original transcript")

            formatted_output = format_output(final_result, output_format)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            
            if keep_audio:
                final_audio_path = output_path.with_suffix('.mp3')
                os.rename(audio_path, final_audio_path)
                click.echo(f"📁 Audio saved to: {final_audio_path}")
            
            click.echo(f"✅ Transcription saved to: {output_path}")

    except Exception as e:
        click.echo(f"❌ Error processing {url}: {str(e)}", err=True)


@click.command()
@click.argument('url', required=False)
@click.option('--input-file', '-i', type=click.Path(exists=True), help='Text file with a list of YouTube URLs to transcribe.')
@click.option('--output-dir', '-o', default='.', help='Output directory for transcripts (default: current directory)')
@click.option('--format', '-f', 'output_format', default='txt', 
              type=click.Choice(['txt', 'srt', 'vtt']), help='Output format (default: txt)')
@click.option('--model', '-m', default='small', 
              type=click.Choice(['tiny', 'base', 'small', 'medium', 'large', 'turbo']), 
              help='Whisper model size')
@click.option('--language', '-l', help='Language code (auto-detect if not specified)')
@click.option('--keep-audio', is_flag=True, help='Keep downloaded audio file')
@click.option('--clean/--no-clean', default=True, help='Clean transcript using LLM (default: clean)')
@click.option('--llm-model', default='gemini-2.0-flash-exp', help='LLM model for cleaning (default: gemini-2.0-flash-exp)')
@click.option('--cleaning-style', type=click.Choice(['presentation', 'conversation', 'lecture']), 
              default='presentation', help='Style of cleaning to apply (default: presentation)')
@click.option('--save-raw', is_flag=True, help='Also save raw transcript before cleaning')
def transcribe(url, input_file, output_dir, output_format, model, language, keep_audio, clean, llm_model, cleaning_style, save_raw):
    """Transcribe one or more YouTube videos to text using OpenAI Whisper."""
    
    if not url and not input_file:
        click.echo("❌ Error: Please provide a URL or an input file with URLs.", err=True)
        raise click.Abort()

    urls = []
    if url:
        urls.append(url)
    
    if input_file:
        with open(input_file, 'r') as f:
            urls.extend([line.strip() for line in f if line.strip()])

    if not urls:
        click.echo("🤷 No URLs to process.", err=True)
        return

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for u in urls:
        process_video(u, output_dir, output_format, model, language, keep_audio, clean, llm_model, cleaning_style, save_raw)
        click.echo("-" * 20)

if __name__ == '__main__':
    transcribe()