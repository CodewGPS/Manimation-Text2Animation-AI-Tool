import chainlit as cl
import openai
import os
import tempfile
import subprocess
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Animation templates for different types of animations
ANIMATION_TEMPLATES = {
    "geometric": """
from manim import *

class GeometricAnimation(Scene):
    def construct(self):
        # Title
        title = Text("{title}", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        {animation_code}
        
        self.wait(2)
""",
    "mathematical": """
from manim import *

class MathematicalAnimation(Scene):
    def construct(self):
        # Title
        title = Text("{title}", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        {animation_code}
        
        self.wait(2)
""",
    "educational": """
from manim import *

class EducationalAnimation(Scene):
    def construct(self):
        # Title
        title = Text("{title}", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        {animation_code}
        
        self.wait(2)
"""
}

@cl.on_chat_start
async def start():
    """Initialize the chat session"""
    # Initialize session state for conversation history
    cl.user_session.set("conversation_history", [])
    cl.user_session.set("animation_count", 0)
    cl.user_session.set("video_quality", "medium")  # Default quality
    
    # Create quality selection buttons
    actions = [
        cl.Action(name="quality_low", label="Low Quality (Fast)", payload={"value": "low"}),
        cl.Action(name="quality_medium", label="Medium Quality", payload={"value": "medium"}),
        cl.Action(name="quality_high", label="High Quality (Slow)", payload={"value": "high"})
    ]
    
    await cl.Message(
        content="Welcome to Text-to-Animation! 🎬\n\nI can create beautiful animations from your descriptions using Manim. Just describe what animation you'd like to see, and I'll generate it for you.\n\nExamples:\n- 'Create a bouncing ball animation'\n- 'Show a circle transforming into a square'\n- 'Animate the quadratic formula'\n- 'Create a 3D cube rotation'\n\n💡 **Tip**: You can ask me to modify previous animations or create variations!\n\n**Select your preferred video quality:**",
        actions=actions
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages and generate animations"""
    
    # Get conversation history and quality setting
    history = cl.user_session.get("conversation_history", [])
    animation_count = cl.user_session.get("animation_count", 0)
    video_quality = cl.user_session.get("video_quality", "medium")
    
    # Add user message to history
    history.append({
        "role": "user",
        "content": message.content,
        "timestamp": datetime.now().isoformat()
    })
    
    # Show typing indicator with quality info
    quality_info = f"🎬 Quality: {video_quality.upper()}"
    thinking_msg = cl.Message(content=f"🤔 Thinking about your animation request... {quality_info}")
    await thinking_msg.send()
    
    try:
        # Generate animation code using OpenAI with context
        animation_code = await generate_animation_code_with_context(message.content, history)
        
        if not animation_code:
            await cl.Message(content="❌ Sorry, I couldn't generate an animation for your request. Please try a different description.").send()
            return
        
        # Create the animation file
        animation_file = await create_animation_file(animation_code)
        
        if not animation_file:
            await cl.Message(content="❌ Failed to create animation file. Please try again.").send()
            return
        
        # Render the animation with selected quality
        video_path = await render_animation(animation_file, video_quality)
        
        if not video_path:
            await cl.Message(content="❌ Failed to render animation. Please try again.").send()
            return
        
        # Send the video to the UI
        await send_video_to_ui(video_path)
        
        # Update session state
        animation_count += 1
        cl.user_session.set("animation_count", animation_count)
        
        # Add assistant response to history
        history.append({
            "role": "assistant",
            "content": f"Created animation #{animation_count}: {message.content}",
            "timestamp": datetime.now().isoformat()
        })
        cl.user_session.set("conversation_history", history)
        
        # Remove thinking message
        await thinking_msg.remove()
        
    except Exception as e:
        await cl.Message(content=f"❌ An error occurred: {str(e)}").send()

@cl.action_callback("quality_low")
async def on_quality_low(action):
    """Handle low quality selection"""
    cl.user_session.set("video_quality", "low")
    await cl.Message(content="✅ Quality set to **LOW** (Fast rendering)").send()

@cl.action_callback("quality_medium")
async def on_quality_medium(action):
    """Handle medium quality selection"""
    cl.user_session.set("video_quality", "medium")
    await cl.Message(content="✅ Quality set to **MEDIUM** (Balanced)").send()

@cl.action_callback("quality_high")
async def on_quality_high(action):
    """Handle high quality selection"""
    cl.user_session.set("video_quality", "high")
    await cl.Message(content="✅ Quality set to **HIGH** (Slow rendering)").send()

async def generate_animation_code_with_context(description: str, history: list) -> str | None:
    """Generate Manim animation code using OpenAI with conversation context"""
    
    system_prompt = """You are an expert Manim animation developer. Generate Python code for Manim animations based on user descriptions.

Key requirements:
1. Use only Manim library imports and functions
2. Create a single Scene class with a construct method
3. Keep animations simple but engaging
4. Use appropriate colors, timing, and effects
5. Include proper wait times between animations
6. Make the code complete and runnable
7. Consider the conversation context when creating animations

Common Manim objects to use:
- Circle(), Square(), Rectangle(), Triangle()
- Text(), MathTex(), Tex()
- Arrow(), Line(), Dot()
- Transform(), Create(), Write(), FadeIn(), FadeOut()
- UP, DOWN, LEFT, RIGHT, ORIGIN
- Colors: RED, BLUE, GREEN, YELLOW, WHITE, BLACK, etc.

Return only the Python code, no explanations."""

    try:
        # Build conversation context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 5 messages for context)
        recent_history = history[-10:] if len(history) > 10 else history
        for msg in recent_history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                messages.append({"role": "assistant", "content": msg["content"]})
        
        # Add current request
        messages.append({"role": "user", "content": f"Create a Manim animation for: {description}"})
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14",
            messages=messages,
            temperature=0.5,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract Python code from markdown code blocks if present
        if content.startswith("```python"):
            # Remove the opening ```python
            content = content[9:]
            # Remove the closing ``` if present
            if content.endswith("```"):
                content = content[:-3]
        elif content.startswith("```"):
            # Remove the opening ```
            content = content[3:]
            # Remove the closing ``` if present
            if content.endswith("```"):
                content = content[:-3]
        
        return content.strip()
        
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

async def generate_animation_code(description: str) -> str | None:
    """Generate Manim animation code using OpenAI (legacy function)"""
    return await generate_animation_code_with_context(description, [])

async def create_animation_file(code: str) -> str | None:
    """Create a temporary Python file with the animation code"""
    
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            return f.name
    except Exception as e:
        print(f"Error creating animation file: {e}")
        return None

async def render_animation(animation_file: str, quality: str = "medium") -> str | None:
    """Render the animation using Manim with specified quality"""
    
    try:
        # Create a temporary directory for this animation
        temp_dir = tempfile.mkdtemp(prefix="manim_")
        temp_dir_path = Path(temp_dir)
        
        print(f"Created temp directory: {temp_dir}")
        
        # Copy the animation file to temp directory
        temp_anim_file = temp_dir_path / "animation.py"
        shutil.copy2(animation_file, temp_anim_file)
        
        print(f"Copied animation file to: {temp_anim_file}")
        
        # Set quality flags based on user selection
        quality_flags = {
            "low": "-ql",      # Quality low (fast)
            "medium": "-qm",    # Quality medium (balanced)
            "high": "-qh"       # Quality high (slow)
        }
        
        quality_flag = quality_flags.get(quality, "-qm")
        print(f"Using quality setting: {quality} ({quality_flag})")
        
        # Run manim command in temp directory
        cmd = [
            "manim", 
            quality_flag,  # Quality setting
            "-o", "output",  # Output filename
            str(temp_anim_file)
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=temp_dir
        )
        
        print(f"Manim stdout: {result.stdout}")
        print(f"Manim stderr: {result.stderr}")
        print(f"Manim return code: {result.returncode}")
        
        if result.returncode == 0:
            # Look for the video file in the temp directory (including subdirectories)
            video_files = list(temp_dir_path.rglob("*.mp4"))
            print(f"Found video files in temp dir: {video_files}")
            
            if video_files:
                # Get the main video file (not partial files)
                main_video = None
                for video_file in video_files:
                    if "partial_movie_files" not in str(video_file):
                        main_video = video_file
                        break
                
                if main_video:
                    print(f"Found main video: {main_video}")
                    return str(main_video)
        
        print(f"Manim error: {result.stderr}")
        return None
        
    except Exception as e:
        print(f"Error rendering animation: {e}")
        return None

async def send_video_to_ui(video_path: str):
    """Send the rendered video to the Chainlit UI"""
    
    try:
        # Check if video file exists
        if not os.path.exists(video_path):
            await cl.Message(content=f"❌ Video file not found at: {video_path}").send()
            return
        
        print(f"Video file found at: {video_path}")
        
        # Create a message with the video
        elements = [
            cl.Video(
                name="animation",
                path=video_path,
                display="inline"
            )
        ]
        
        await cl.Message(
            content="🎬 Here's your animation!",
            elements=elements
        ).send()
        
        # Clean up the temp directory after sending the video
        try:
            temp_dir = Path(video_path).parent
            if temp_dir.name.startswith("manim_"):
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temp directory: {temp_dir}")
        except Exception as cleanup_error:
            print(f"Error cleaning up temp directory: {cleanup_error}")
            
    except Exception as e:
        await cl.Message(content=f"❌ Error displaying video: {str(e)}").send()
        print(f"Error in send_video_to_ui: {e}")

if __name__ == "__main__":
    cl.run()