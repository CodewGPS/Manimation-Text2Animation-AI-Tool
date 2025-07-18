# Text-to-Animation AI Tool

This project is an AI-powered tool that generates dynamic animations from natural language descriptions using generative AI and the Manim library[1]. It leverages OpenAI's models to create Manim-compatible Python code, renders animations with customizable quality levels, and delivers them through an interactive Chainlit chat interface[1].

## Features

- **Natural Language Input**: Users describe animations in plain English, such as "Create a bouncing ball animation" or "Animate the quadratic formula," and the tool generates corresponding Manim code[1].
- **Quality Controls**: Select from low, medium, or high quality via interactive buttons, balancing rendering speed and output fidelity[1].
- **Context-Aware Conversations**: Maintains conversation history for modifications or variations across multiple exchanges, using up to the last 10 messages for context[1].
- **Real-Time Rendering and Delivery**: Processes requests, renders videos using Manim, and streams results inline in the chat, with temporary file management for efficiency[1].
- **Error Handling**: Includes comprehensive checks for code generation, file creation, rendering, and cleanup, ensuring reliability[1].

## Installation

1. Clone the repository:
   ```
   git clone 
   cd text-to-animation-tool
   ```

2. Install dependencies from `requirements.txt`:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add your OpenAI API key: `OPENAI_API_KEY=your-api-key-here`[1].

## Usage

1. Run the application:
   ```
   chainlit run app.py
   ```

2. Access the chat interface in your browser (typically at `http://localhost:8000`).

3. Select video quality using the provided buttons.

4. Enter a description and receive the generated animation video directly in the chat[1].

## Configuration

- **Video Quality**: Defaults to "medium." Change via chat buttons for low (fast), medium (balanced), or high (detailed but slower) rendering[1].
- **Manim Rendering**: Uses flags like `-ql`, `-qm`, `-qh` for quality, outputting MP4 files[1].
- **OpenAI Model**: Configured with `gpt-4.1-mini-2025-04-14` for code generation, with a temperature of 0.5 and max tokens of 1000[1].

## How It Works

The tool initializes a Chainlit session, handles user messages by generating Manim code via OpenAI with conversation context, creates temporary Python files, renders animations in isolated directories, and sends videos while cleaning up resources[1].

## Contributing

Contributions are welcome. Fork the repository, make changes, and submit a pull request.

## License

This project is licensed under the MIT License.

[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/81487501/2e2fc247-afe9-42e2-92e9-e75a36903c17/app.py
