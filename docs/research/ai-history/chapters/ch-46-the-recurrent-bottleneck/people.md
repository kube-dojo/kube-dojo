# People: Chapter 46 - The Recurrent Bottleneck

## Core Actors

- **Sepp Hochreiter** - Co-author of the 1997 LSTM paper; his 1991 diploma thesis is the cited origin point for the vanishing/exploding-gradient analysis summarized in Hochreiter & Schmidhuber 1997.
- **Jurgen Schmidhuber** - Co-author of the 1997 LSTM paper and the 2000 forget-gate paper; IDSIA affiliation in the 1997 source.
- **Yoshua Bengio** - Co-author of the 1994 long-dependency paper and later co-author of the 2016 *Deep Learning* textbook used here as secondary framing.
- **Patrice Simard and Paolo Frasconi** - Co-authors with Bengio on the 1994 paper that independently formalized the difficulty of learning long-term dependencies with gradient descent.
- **Felix A. Gers and Fred Cummins** - Co-authors with Schmidhuber on the 2000 paper that introduced the adaptive forget gate for continual LSTM streams.

## System Builders

- **Alex Graves, Abdel-rahman Mohamed, and Geoffrey Hinton** - Authors of the 2013 deep recurrent speech-recognition paper; useful for showing that LSTM was a successful applied architecture before the Transformer.
- **Ilya Sutskever, Oriol Vinyals, and Quoc V. Le** - Authors of the 2014 sequence-to-sequence LSTM paper; provide the chapter's strongest pre-GNMT infrastructure scene: deep LSTMs, 8 GPUs, 6,300 words/sec, ten-day training.
- **Yonghui Wu, Mike Schuster, Zhifeng Chen, Quoc V. Le, Jeffrey Dean, and the GNMT author group** - Authors of the 2016 Google NMT paper; anchor the production-scale recurrent stack and its model-parallel engineering constraints.
- **Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, and Illia Polosukhin** - Authors of "Attention Is All You Need"; in this chapter they are used only for the bottleneck diagnosis and transition, not for the full Transformer story.

## Handling Notes

- Do not imply that any single person "caused" the shift away from recurrence. The evidence supports a technical constraint narrative, not a heroic replacement story.
- Keep "Hinton" in this chapter tied to Graves/Mohamed/Hinton 2013 and textbook/secondary context, not as a generic authority for all recurrent-network history.
- If prose mentions Google, distinguish Google Brain/Google Research author affiliations in the Transformer paper from the broader Google Translate/GNMT production system.
