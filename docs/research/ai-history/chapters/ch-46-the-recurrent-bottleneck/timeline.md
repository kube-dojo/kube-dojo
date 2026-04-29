# Timeline: Chapter 46 - The Recurrent Bottleneck

- **1991:** Sepp Hochreiter's diploma thesis analyzes why error signals in recurrent networks can vanish or explode over long time lags. The thesis itself is not extracted here; Hochreiter & Schmidhuber 1997 summarize the analysis and cite thesis pp. 19-21.
- **1994:** Bengio, Simard, and Frasconi publish "Learning long-term dependencies with gradient descent is difficult" in *IEEE Transactions on Neural Networks* 5(2), pp. 157-166, DOI `10.1109/72.279181`.
- **1997:** Hochreiter and Schmidhuber publish "Long Short-Term Memory" in *Neural Computation* 9(8), pp. 1735-1780, introducing LSTM, constant error carousels, and multiplicative gates.
- **2000:** Gers, Schmidhuber, and Cummins publish "Learning to Forget: Continual Prediction with LSTM" in *Neural Computation* 12(10), pp. 2451-2471, introducing the adaptive forget gate for continual streams.
- **2013:** Graves, Mohamed, and Hinton publish "Speech Recognition with Deep Recurrent Neural Networks," reporting deep LSTM RNN results on the TIMIT phoneme benchmark.
- **2014:** Sutskever, Vinyals, and Le publish "Sequence to Sequence Learning with Neural Networks," using multilayer LSTM encoder/decoder models for WMT'14 English-French translation and an 8-GPU implementation.
- **2016:** Wu et al. publish "Google's Neural Machine Translation System," a production-oriented deep LSTM encoder/decoder system with attention, residual connections, wordpieces, model parallelism, and low-precision inference.
- **June 12, 2017:** Vaswani et al. submit "Attention Is All You Need" to arXiv, explicitly naming the sequential parallelization constraint of recurrent models.
- **2017 onward:** The Transformer story belongs to Ch50; Chapter 46 should stop at the recurrent bottleneck and point forward.
