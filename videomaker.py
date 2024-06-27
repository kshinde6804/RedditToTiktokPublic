import click
import json
import numpy as np
from redditscraper import getContent, get_post_image, byte_to_char_offset
from moviepy.editor import VideoClip, TextClip, ImageClip, concatenate_videoclips, concatenate_audioclips, VideoFileClip, CompositeVideoClip, ColorClip, AudioFileClip
import moviepy
import moviepy.video.fx.all as vfx
import boto3
from awspolly import synthesize_speech, get_speech_audio
import random
from PIL import Image
import re

@click.command()
@click.option(
    "--videos", "videos", default=1, help="Number of videos to make.", type=int
)
@click.option(
    "--num_comments", "num_comments", default=7, help="Number of comments to use.", type=int
)
@click.option(
    "--subreddit",
    "subreddit",
    default="AskReddit",
    help="Subreddit to get videos from.",
    type=str,
)
@click.option(
    "--text", 
    "text", 
    default="comment", 
    help="Type of content, comment/body text.", 
    type=str,
)
@click.option(
    "--duration", 
    "duration", 
    default="20", 
    help="Desired length of video in seconds.", 
    type=int,
)
@click.option(
    "--media_type", 
    "media_type", 
    default="Tiktok", 
    help="Type of media intended to upload, changes video dimensions. Options are Youtube for full screen (works rn) or TikTok for phone screen (doesn't).", 
    type=str,
)

def main(videos: int, subreddit: str, text: str, num_comments: int, duration: int, media_type: str):
    """Automatically generate videos from Reddit posts."""
    make_video(videos, subreddit, text, num_comments, duration, media_type)

def make_video(videos=1, subreddit="AskReddit", text="comment", num_comments=10, duration=20, media_type="Tiktok"):
    print(f"Generating {videos} videos from r/{subreddit}.")
    titles, contents, post_ids = getContent(subreddit, videos, text, num_comments)
    clip_width = 1000
    clip_height = 1000
    for t in titles:
        print(t)
    for id in post_ids:
        print(id)
    video_list = []
    if (media_type == "Tiktok"):
        clip_width = 1080
        clip_height = 1920
        
        

    for i in range(videos):
        text_clips = []

        
        # Get the image of the post
        post_image_path = get_post_image(subreddit, post_ids[i], media_type)

        title_audio_clip, title_duration = create_title(text_clips, titles[i], post_image_path, i, clip_width, clip_height)

        # Get enough video content to create a video of a desired duration
        video_content = set_video_content(contents[i], title_duration, duration)
        
        print(f"Creating video {i+1} with post ID: {post_ids[i]}")


        # Convert body text into audio and metadata
        word_timings = synthesize_speech_helper(video_content, f'text_audio_{i}.mp3', f'text_marks_{i}.json')
        text_audio_clip = AudioFileClip(f'text_audio_{i}.mp3')
        

        # Handle break times and create text clips
        compile_video_contents(video_content, text_clips, word_timings, title_duration, text_audio_clip, clip_width, clip_height)

        video_clip = concatenate_videoclips(text_clips, method="compose")
        final_audio_clip = concatenate_audioclips([title_audio_clip, text_audio_clip])
        total_duration = video_clip.duration

        masked_video_clip = vfx.mask_color(video_clip, color=[165, 42, 42], thr=10, s=1)

        if (media_type == "Tiktok"):
            youtube_videos = ["minecraftparkourvideoTiktok.mp4"]
        else:
            youtube_videos = ["subwaysurfersvideo.mp4", "minecraftparkourvideo.mp4"] # Add more videos to this
        num_youtube_videos = len(youtube_videos)

        video_selection = random.randint(0, num_youtube_videos - 1)
        # Load the YouTube clip to get its duration
        youtube_clip = VideoFileClip(youtube_videos[video_selection])
        youtube_duration = youtube_clip.duration

        # Ensure the random start time is within the bounds of the YouTube clip duration
        random_start_time = random.randint(-2, int(youtube_duration - total_duration))
        try:
            youtube_clip = youtube_clip.subclip(random_start_time, random_start_time + total_duration)

            final_clip = CompositeVideoClip([youtube_clip.set_start(0), masked_video_clip.set_start(0).set_position('center')])
            final_clip = final_clip.set_audio(final_audio_clip)
            # Resize the final clip if media_type is TikTok
            if media_type == "TikTok":
                final_clip = final_clip.resize(newsize=(1080, 1920))

            print("Writing videofile...")
            final_clip.write_videofile(f"final_video_{i+1}.mp4", fps=24, codec="libx264")
            print("Finished writing.")
            video_list.append(f"final_video_{i+1}.mp4")

        finally:
            print("Closing...")
            video_clip.close()
            youtube_clip.close()
            final_clip.close()
            print("Closed.")
    return video_list

def set_video_content(contents, title_duration, desired_length):
    j = 0
    curr_length = title_duration
    video_content = ""
    while (j < len(contents) and curr_length < desired_length):
        # Remove URLs starting with "https:"
        contents[j] = re.sub(r"https:[^\s]*", "", contents[j])
        if (contents[j] != "removed"):
            get_speech_audio(contents[j],"temp_audio.mp3")
            clip_time = AudioFileClip("temp_audio.mp3").duration
            curr_length += clip_time
            video_content += (f" {j+1}. {contents[j]}.")
        j += 1
    if (j == 1):
        video_content = f"{contents[j]}."
    return (video_content + " <break time='1s'/> ")

def create_title(text_clips, title, post_image_path, i, clip_width, clip_height):
    # Convert title text into audio and metadata
    title_word_timings = synthesize_speech_helper(title, f'title_audio_{i}.mp3', f'title_marks_{i}.json')

    # Use length of title audio to set title frame duration
    title_audio_clip = AudioFileClip(f'title_audio_{i}.mp3')
    title_duration = title_audio_clip.duration

    
    # Create a brown background ColorClip to remove title background
    background_clip = ColorClip(size=(clip_width, clip_height), color=(165, 42, 42)).set_duration(title_duration)

    # Overlay the ImageClip on the background
    title_clip = ImageClip(post_image_path).set_duration(title_duration)
    
    if (clip_width == 1080):
        # Resize the title image to fit within the dimensions of the video
        title_clip = title_clip.resize(height=clip_height)  # Adjust the height to leave some padding
        title_clip = title_clip.resize(width=clip_width*(9/16)+100)  # Further resize if width exceeds the clip width


    composite_clip = CompositeVideoClip([background_clip, title_clip.set_position('center')])

    text_clips.append(composite_clip)
    return title_audio_clip, title_duration


def synthesize_speech_helper(video_content, audio_file_name, mark_file_name):
    text_to_synthesize = video_content
    text_output_audio_file = audio_file_name
    text_output_marks_file = mark_file_name
    print(f"Text audio content written to file {text_output_audio_file}")
    return synthesize_speech(text_to_synthesize, text_output_audio_file, text_output_marks_file)
    

def compile_video_contents(video_content, text_clips, word_timings, title_duration, text_audio_clip, clip_width, clip_height):
    #Set TextClip parameters
    font_name = "Cooper-Black"
    stroke_color_ = "black"
    stroke_width_ = 3
    kerning_width = -3
    background_color = "brown"
    nsfw_words = ["fuck", "shit", "cunt", "bitch", "asshole", "dick", "pussy", "bastard", "slut", "whore", "fag", "dyke", "nigger", "nigga", "cock", "cum", "jizz", "dildo", "penis", "vagina", "boobs", "tits", "tit", "clit", "clitoris", "blowjob", "handjob", "rimjob", "anal", "tranny", "trannies"]
    #Initialize variables
    word_duration = 0
    line_length = 0
    words_in_line = 0
    start_time = title_duration
    line = ""
    line_start = 0
    desired_line_length = 5
    punctuation_marks = ['.', ',', '?', '!', ';']
    
    # Handle break times and create text clips
    for j, mark in enumerate(word_timings):
        word = mark['value']
        #Create running line up until set limit
        line += (word + " ")
        line_length += (len(word) + 1)
        words_in_line += 1
        word_start = mark['time'] / 1000.0  # Convert milliseconds to seconds

        #
        if words_in_line == 1:
            line_start = word_start

        # print(line)
        if word.lower() in nsfw_words:
            word = word[0] + "*" * (len(word) - 1)


        if "time='1s'" in line:
            line_length = 0
            words_in_line = 0
            line = ""
            continue

        if "break" in line:
            if (j < len(word_timings) - 1 and "time='1s'" in word_timings[j + 1]['value']):
                # Remove break from that line, add the rest of the line to its own frame, then proceed
                line = line[:-6]
                
                #If there were other characters than break, then process them
                if (line):
                    word_duration = word_start - line_start
                    create_text_clip(line, text_clips, word_duration, start_time, line_start, clip_width, clip_height)

                break_clip = ColorClip(size=(clip_width, clip_height), color=(165, 42, 42, 255)).set_duration(1).set_start(start_time + line_start + word_duration)

                text_clips.append(break_clip)
                
                line_length = 0
                words_in_line = 0
                line = ""
                line_start += 1
                continue

        next_word_end = mark['end'] if j < len(word_timings) - 1 else len(video_content)
        char_offset = byte_to_char_offset(video_content, next_word_end)

        if (char_offset < len(video_content) and video_content[char_offset] in punctuation_marks):
            line = line[:-1]
            line += video_content[char_offset]
            line_length += 1

            if j < len(word_timings) - 1:
                next_word_start = word_timings[j + 1]['time'] / 1000.0
            else:
                next_word_start = text_audio_clip.duration + title_duration

            word_duration = next_word_start - line_start

            create_text_clip(line, text_clips, word_duration, start_time, line_start, clip_width, clip_height)
            
            line_length = 0
            words_in_line = 0
            line = ""
            line_start = next_word_start
        #Need to handle case of number that is 2+ words (1997, 128)
        elif line_length >= desired_line_length:
            if j < len(word_timings) - 1:
                next_word_start = word_timings[j + 1]['time'] / 1000.0
            else:
                next_word_start = text_audio_clip.duration + title_duration

            word_duration = next_word_start - line_start

            create_text_clip(line, text_clips, word_duration, start_time, line_start, clip_width, clip_height)

            line_length = 0
            words_in_line = 0
            line = ""
            line_start = next_word_start

    if line:
        text_clip = TextClip(line.strip(), fontsize=65, font=font_name, kerning=kerning_width, bg_color=background_color, color='white', stroke_color=stroke_color_, stroke_width=stroke_width_, size=(clip_width, clip_height), method='caption')
        text_clip = text_clip.set_start(start_time + line_start).set_duration(text_audio_clip.duration - line_start + title_duration)
        text_clips.append(text_clip)

def custom_resize(image, new_size):
    """Resize the image using PIL's LANCZOS filter."""
    pil_image = Image.fromarray(image)
    return np.array(pil_image.resize(new_size, Image.LANCZOS))


def create_text_clip(line, text_clips, word_duration, start_time, line_start, clip_width, clip_height):
    font_name = "Cooper-Black"
    stroke_color_ = "black"
    stroke_width_ = 3
    kerning_width = -3
    background_color = "brown"

    # Create the text clip
    text_clip = TextClip(line.strip(), fontsize=65, font=font_name, kerning=kerning_width, bg_color=background_color, color='white', stroke_color=stroke_color_, stroke_width=stroke_width_, size=(clip_width, clip_height), method='caption')

    # Duration of the text clip
    duration = word_duration

    # Define the scaling function for text resizing
    def resize(t, duration):
        # Define starting and ending scale factors
        start_scale = 1
        end_scale = 2
        # Compute the scaling factor linearly over the clip's duration
        scale_factor = start_scale + (t / duration) * (end_scale - start_scale)
        return scale_factor

    # Define the positioning function to center the text
    def translate(t, duration, screen_size):
        # Calculate the current scale at time t
        current_scale = resize(t, duration)
        # Get the original dimensions of the screen
        screen_width, screen_height = screen_size
        # Calculate the position to keep the text centered after scaling
        x = (screen_width * current_scale) / 2
        y = (screen_height * current_scale) / 2
        return (x, y)

    # Function to apply the resizing effect
    def apply_effects(clip, duration, screen_size):
        return clip.fl_time(lambda t: t, apply_to=['mask', 'video'])\
                .fl(lambda gf, t: custom_resize(gf(t), (int(gf(t).shape[1] * resize(t, duration)),
                                                            int(gf(t).shape[0] * resize(t, duration)))))\
                .set_position(lambda t: translate(t, duration, screen_size))


    screen_size = (clip_width, clip_height)
    # Apply the popping out effect with scaling and centering
    text_clip = text_clip.set_start(start_time + line_start).set_duration(word_duration)
    # text_clip = apply_effects(text_clip, word_duration, screen_size)

    text_clips.append(text_clip)

def get_video_content(text, content, text_clips):
    #Change this up. have getContent() return all 4 pieces of data. 
    # For body text, return the body text and num_comments comments in video_content, 
    # and for comment text, just return num_comments comments
    # ALSO, just used some delimiter before <break time>. Like have NEWCOMMENT, and just check for that???
    if text == "comment":
        combined_comments = ""
        for comment in content:
            combined_comments += (comment.body + " <break time='1s'/> ")
        video_content = combined_comments
    elif text == "body":
        video_content = content[i]
    else:
        video_content = "Error creating video_content in get_video_content"
        print("Invalid text type, please enter either comment or body")
        exit(1)

    return video_content


if __name__ == "__main__":
    main()
