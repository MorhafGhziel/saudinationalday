/**
 * Original ambience, synthesised in the browser: filtered noise that breathes like wind, a soft swell
 * for travel and a tiny tick for choices. Nothing plays until the visitor turns sound on.
 * (Made by code and checked by measurement only: it has not been judged by ear.)
 */
export class Sound {
  private ctx: AudioContext | null = null;
  private master!: GainNode;
  private wind!: BiquadFilterNode;
  on = false;

  private boot() {
    if (this.ctx) return;
    const ctx = (this.ctx = new AudioContext());
    this.master = ctx.createGain(); this.master.gain.value = 0; this.master.connect(ctx.destination);
    const len = ctx.sampleRate * 4, buf = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let c = 0; c < 2; c++) { const d = buf.getChannelData(c); let last = 0; for (let i = 0; i < len; i++) { last = last * 0.985 + (Math.random() * 2 - 1) * 0.015; d[i] = last * 9; } }   // brown-ish noise
    const src = ctx.createBufferSource(); src.buffer = buf; src.loop = true;
    this.wind = ctx.createBiquadFilter(); this.wind.type = "bandpass"; this.wind.frequency.value = 420; this.wind.Q.value = 0.6;
    const lfo = ctx.createOscillator(); lfo.frequency.value = 0.07; const depth = ctx.createGain(); depth.gain.value = 180;
    lfo.connect(depth).connect(this.wind.frequency); lfo.start();
    const g = ctx.createGain(); g.gain.value = 0.5;
    src.connect(this.wind).connect(g).connect(this.master); src.start();
  }
  async toggle() {
    this.boot();
    this.on = !this.on;
    await this.ctx!.resume();
    this.master.gain.setTargetAtTime(this.on ? 0.22 : 0, this.ctx!.currentTime, 0.6);
    return this.on;
  }
  /** A slow swell while travelling: the wind opens up, then settles. */
  swell(seconds: number) {
    if (!this.on || !this.ctx) return;
    const t = this.ctx.currentTime, f = this.wind.frequency;
    f.cancelScheduledValues(t); f.setTargetAtTime(1100, t, seconds * 0.25); f.setTargetAtTime(420, t + seconds * 0.6, seconds * 0.3);
  }
  tick() {
    if (!this.on || !this.ctx) return;
    const t = this.ctx.currentTime, o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.type = "sine"; o.frequency.value = 660; g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.06, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.18);
    o.connect(g).connect(this.master); o.start(t); o.stop(t + 0.2);
  }
}
