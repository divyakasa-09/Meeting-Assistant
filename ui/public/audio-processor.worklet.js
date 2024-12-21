class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
      super();
      this.silenceCounter = 0;
      this.lastSentTime = 0;
      this.SILENCE_THRESHOLD = 0.01;
      this.MAX_SILENCE_DURATION = 1000; // 1 second
    }
  
    process(inputs, outputs, parameters) {
      const input = inputs[0][0];
      if (!input) return true;
  
      const maxLevel = Math.max(...input.map(Math.abs));
      const currentTime = currentFrame / sampleRate * 1000;
  
      // Create audio data
      const int16Array = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]));
        int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
  
      // Send data if we have audio or enough silence has passed
      if (maxLevel > this.SILENCE_THRESHOLD || (currentTime - this.lastSentTime) > this.MAX_SILENCE_DURATION) {
        this.port.postMessage({
          type: 'audio',
          buffer: int16Array.buffer
        }, [int16Array.buffer]);
  
        this.lastSentTime = currentTime;
        this.silenceCounter = 0;
      } else {
        this.silenceCounter++;
        
        // Send minimal silence packet periodically
        if (this.silenceCounter >= 24) {
          const silenceBuffer = new Int16Array(160).fill(0);
          this.port.postMessage({
            type: 'silence',
            buffer: silenceBuffer.buffer
          }, [silenceBuffer.buffer]);
          this.silenceCounter = 0;
          this.lastSentTime = currentTime;
        }
      }
  
      // Copy input to output
      for (let channel = 0; channel < outputs.length; channel++) {
        outputs[channel][0].set(input);
      }
  
      return true;
    }
  }
  
  registerProcessor('audio-processor', AudioProcessor);