# Infrastructure Log: Chapter 52

## Technical Metrics & Constraints
- **Model sizes:**
  - BERTBASE: 12 layers, hidden size 768, 12 attention heads, 110M parameters.
  - BERTLARGE: 24 layers, hidden size 1024, 16 attention heads, 340M parameters.

- **Input representation:**
  - WordPiece embeddings with a 30,000 token vocabulary.
  - Input representation sums token, segment, and position embeddings.
  - Sentence pairs use [SEP] and learned sentence A/B segment embeddings; [CLS] is used as aggregate representation for classification.

- **Pre-training corpus:**
  - BooksCorpus: 800M words.
  - English Wikipedia: 2,500M words.
  - Paper emphasizes document-level corpus for long contiguous sequences.

- **Pre-training hardware and time:**
  - BERTBASE: 4 Cloud TPUs in Pod configuration, 16 TPU chips total.
  - BERTLARGE: 16 Cloud TPUs, 64 TPU chips total.
  - Each pre-training run took 4 days.

- **Fine-tuning economics:**
  - Paper says fine-tuning is relatively inexpensive compared with pre-training.
  - All paper results can be replicated in at most 1 hour on a single Cloud TPU or a few hours on a GPU, starting from the same pre-trained model.
  - Google blog says a state-of-the-art question answering system can be trained in about 30 minutes on a single Cloud TPU or a few hours on a single GPU.

- **Release artifact:**
  - Google blog: release includes TensorFlow source code and pre-trained language representation models.
  - GitHub API extraction on 2026-04-28: `google-research/bert` created 2018-10-25.
  - Treat the repository/checkpoint as a bridge from paper/code distribution to later model-hub infrastructure, not as a full Chapter 54 substitute.

## Do Not Say

- Do not translate hardware time into dollar cost without a source.
- Do not say fine-tuning equals training BERT from scratch.
- Do not say BERT "understands" language in an unqualified human sense.
