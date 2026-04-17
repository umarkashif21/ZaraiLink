---
tags:
- setfit
- sentence-transformers
- text-classification
- generated_from_setfit_trainer
widget:
- text: want to sell wheat
- text: wheat bulk selling price negotiable
- text: palm oil exporter malaysia bulk shipment
- text: sugar supplier pakistan wholesale rate
- text: bulk garlic supplier from iran
metrics:
- accuracy
pipeline_tag: text-classification
library_name: setfit
inference: true
base_model: sentence-transformers/paraphrase-MiniLM-L6-v2
model-index:
- name: SetFit with sentence-transformers/paraphrase-MiniLM-L6-v2
  results:
  - task:
      type: text-classification
      name: Text Classification
    dataset:
      name: Unknown
      type: unknown
      split: test
    metrics:
    - type: accuracy
      value: 1.0
      name: Accuracy
---

# SetFit with sentence-transformers/paraphrase-MiniLM-L6-v2

This is a [SetFit](https://github.com/huggingface/setfit) model that can be used for Text Classification. This SetFit model uses [sentence-transformers/paraphrase-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L6-v2) as the Sentence Transformer embedding model. A [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) instance is used for classification.

The model has been trained using an efficient few-shot learning technique that involves:

1. Fine-tuning a [Sentence Transformer](https://www.sbert.net) with contrastive learning.
2. Training a classification head with features from the fine-tuned Sentence Transformer.

## Model Details

### Model Description
- **Model Type:** SetFit
- **Sentence Transformer body:** [sentence-transformers/paraphrase-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L6-v2)
- **Classification head:** a [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) instance
- **Maximum Sequence Length:** 128 tokens
- **Number of Classes:** 2 classes
<!-- - **Training Dataset:** [Unknown](https://huggingface.co/datasets/unknown) -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Repository:** [SetFit on GitHub](https://github.com/huggingface/setfit)
- **Paper:** [Efficient Few-Shot Learning Without Prompts](https://arxiv.org/abs/2209.11055)
- **Blogpost:** [SetFit: Efficient Few-Shot Learning Without Prompts](https://huggingface.co/blog/setfit)

### Model Labels
| Label | Examples                                                                                                                                          |
|:------|:--------------------------------------------------------------------------------------------------------------------------------------------------|
| SELL  | <ul><li>'koi maize ka buyer hai africa mein?'</li><li>'who buys wheat'</li><li>'palm oil sellers targeting indonesia buyers'</li></ul>            |
| BUY   | <ul><li>'soybean bulk importer pakistan'</li><li>'sourcing garlic in bulk cheap rate'</li><li>'who supplies rock salt in bulk pakistan'</li></ul> |

## Evaluation

### Metrics
| Label   | Accuracy |
|:--------|:---------|
| **all** | 1.0      |

## Uses

### Direct Use for Inference

First install the SetFit library:

```bash
pip install setfit
```

Then you can load this model and run inference.

```python
from setfit import SetFitModel

# Download from the 🤗 Hub
model = SetFitModel.from_pretrained("setfit_model_id")
# Run inference
preds = model("want to sell wheat")
```

<!--
### Downstream Use

*List how someone could finetune this model on their own dataset.*
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Set Metrics
| Training set | Min | Median | Max |
|:-------------|:----|:-------|:----|
| Word count   | 2   | 5.1357 | 9   |

| Label | Training Sample Count |
|:------|:----------------------|
| BUY   | 139                   |
| SELL  | 141                   |

### Training Hyperparameters
- batch_size: (16, 16)
- num_epochs: (3, 3)
- max_steps: -1
- sampling_strategy: oversampling
- body_learning_rate: (2e-05, 1e-05)
- head_learning_rate: 0.01
- loss: CosineSimilarityLoss
- distance_metric: cosine_distance
- margin: 0.25
- end_to_end: False
- use_amp: False
- warmup_proportion: 0.1
- l2_weight: 0.01
- seed: 42
- evaluation_strategy: epoch
- eval_max_steps: -1
- load_best_model_at_end: False

### Training Results
| Epoch  | Step | Training Loss | Validation Loss |
|:------:|:----:|:-------------:|:---------------:|
| 0.0004 | 1    | 0.4029        | -               |
| 0.0203 | 50   | 0.2832        | -               |
| 0.0405 | 100  | 0.2519        | -               |
| 0.0608 | 150  | 0.2422        | -               |
| 0.0810 | 200  | 0.2143        | -               |
| 0.1013 | 250  | 0.1534        | -               |
| 0.1216 | 300  | 0.0859        | -               |
| 0.1418 | 350  | 0.0405        | -               |
| 0.1621 | 400  | 0.0137        | -               |
| 0.1823 | 450  | 0.0067        | -               |
| 0.2026 | 500  | 0.0039        | -               |
| 0.2229 | 550  | 0.0021        | -               |
| 0.2431 | 600  | 0.0023        | -               |
| 0.2634 | 650  | 0.0011        | -               |
| 0.2836 | 700  | 0.0008        | -               |
| 0.3039 | 750  | 0.0007        | -               |
| 0.3241 | 800  | 0.0005        | -               |
| 0.3444 | 850  | 0.0005        | -               |
| 0.3647 | 900  | 0.0005        | -               |
| 0.3849 | 950  | 0.0005        | -               |
| 0.4052 | 1000 | 0.0004        | -               |
| 0.4254 | 1050 | 0.0004        | -               |
| 0.4457 | 1100 | 0.0003        | -               |
| 0.4660 | 1150 | 0.0008        | -               |
| 0.4862 | 1200 | 0.0003        | -               |
| 0.5065 | 1250 | 0.0004        | -               |
| 0.5267 | 1300 | 0.0003        | -               |
| 0.5470 | 1350 | 0.0003        | -               |
| 0.5673 | 1400 | 0.0002        | -               |
| 0.5875 | 1450 | 0.0003        | -               |
| 0.6078 | 1500 | 0.0003        | -               |
| 0.6280 | 1550 | 0.0002        | -               |
| 0.6483 | 1600 | 0.0002        | -               |
| 0.6686 | 1650 | 0.0005        | -               |
| 0.6888 | 1700 | 0.0004        | -               |
| 0.7091 | 1750 | 0.0002        | -               |
| 0.7293 | 1800 | 0.0002        | -               |
| 0.7496 | 1850 | 0.0002        | -               |
| 0.7699 | 1900 | 0.0002        | -               |
| 0.7901 | 1950 | 0.0002        | -               |
| 0.8104 | 2000 | 0.0008        | -               |
| 0.8306 | 2050 | 0.0002        | -               |
| 0.8509 | 2100 | 0.0009        | -               |
| 0.8712 | 2150 | 0.0002        | -               |
| 0.8914 | 2200 | 0.0002        | -               |
| 0.9117 | 2250 | 0.0001        | -               |
| 0.9319 | 2300 | 0.0002        | -               |
| 0.9522 | 2350 | 0.0001        | -               |
| 0.9724 | 2400 | 0.0001        | -               |
| 0.9927 | 2450 | 0.0001        | -               |
| 1.0    | 2468 | -             | 0.0000          |
| 1.0130 | 2500 | 0.0001        | -               |
| 1.0332 | 2550 | 0.0001        | -               |
| 1.0535 | 2600 | 0.0001        | -               |
| 1.0737 | 2650 | 0.0001        | -               |
| 1.0940 | 2700 | 0.0001        | -               |
| 1.1143 | 2750 | 0.0001        | -               |
| 1.1345 | 2800 | 0.0001        | -               |
| 1.1548 | 2850 | 0.0001        | -               |
| 1.1750 | 2900 | 0.0001        | -               |
| 1.1953 | 2950 | 0.0001        | -               |
| 1.2156 | 3000 | 0.0001        | -               |
| 1.2358 | 3050 | 0.0001        | -               |
| 1.2561 | 3100 | 0.0001        | -               |
| 1.2763 | 3150 | 0.0001        | -               |
| 1.2966 | 3200 | 0.0001        | -               |
| 1.3169 | 3250 | 0.0001        | -               |
| 1.3371 | 3300 | 0.0001        | -               |
| 1.3574 | 3350 | 0.0001        | -               |
| 1.3776 | 3400 | 0.0001        | -               |
| 1.3979 | 3450 | 0.0001        | -               |
| 1.4182 | 3500 | 0.0001        | -               |
| 1.4384 | 3550 | 0.0001        | -               |
| 1.4587 | 3600 | 0.0001        | -               |
| 1.4789 | 3650 | 0.0001        | -               |
| 1.4992 | 3700 | 0.0001        | -               |
| 1.5194 | 3750 | 0.0001        | -               |
| 1.5397 | 3800 | 0.0001        | -               |
| 1.5600 | 3850 | 0.0001        | -               |
| 1.5802 | 3900 | 0.0001        | -               |
| 1.6005 | 3950 | 0.0001        | -               |
| 1.6207 | 4000 | 0.0001        | -               |
| 1.6410 | 4050 | 0.0001        | -               |
| 1.6613 | 4100 | 0.0001        | -               |
| 1.6815 | 4150 | 0.0001        | -               |
| 1.7018 | 4200 | 0.0001        | -               |
| 1.7220 | 4250 | 0.0001        | -               |
| 1.7423 | 4300 | 0.0001        | -               |
| 1.7626 | 4350 | 0.0001        | -               |
| 1.7828 | 4400 | 0.0001        | -               |
| 1.8031 | 4450 | 0.0001        | -               |
| 1.8233 | 4500 | 0.0001        | -               |
| 1.8436 | 4550 | 0.0001        | -               |
| 1.8639 | 4600 | 0.0001        | -               |
| 1.8841 | 4650 | 0.0001        | -               |
| 1.9044 | 4700 | 0.0001        | -               |
| 1.9246 | 4750 | 0.0001        | -               |
| 1.9449 | 4800 | 0.0001        | -               |
| 1.9652 | 4850 | 0.0001        | -               |
| 1.9854 | 4900 | 0.0001        | -               |
| 2.0    | 4936 | -             | 0.0000          |
| 2.0057 | 4950 | 0.0001        | -               |
| 2.0259 | 5000 | 0.0001        | -               |
| 2.0462 | 5050 | 0.0001        | -               |
| 2.0665 | 5100 | 0.0001        | -               |
| 2.0867 | 5150 | 0.0001        | -               |
| 2.1070 | 5200 | 0.0001        | -               |
| 2.1272 | 5250 | 0.0001        | -               |
| 2.1475 | 5300 | 0.0001        | -               |
| 2.1677 | 5350 | 0.0001        | -               |
| 2.1880 | 5400 | 0.0001        | -               |
| 2.2083 | 5450 | 0.0001        | -               |
| 2.2285 | 5500 | 0.0001        | -               |
| 2.2488 | 5550 | 0.0001        | -               |
| 2.2690 | 5600 | 0.0002        | -               |
| 2.2893 | 5650 | 0.0001        | -               |
| 2.3096 | 5700 | 0.0001        | -               |
| 2.3298 | 5750 | 0.0001        | -               |
| 2.3501 | 5800 | 0.0001        | -               |
| 2.3703 | 5850 | 0.0001        | -               |
| 2.3906 | 5900 | 0.0001        | -               |
| 2.4109 | 5950 | 0.0001        | -               |
| 2.4311 | 6000 | 0.0001        | -               |
| 2.4514 | 6050 | 0.0001        | -               |
| 2.4716 | 6100 | 0.0001        | -               |
| 2.4919 | 6150 | 0.0001        | -               |
| 2.5122 | 6200 | 0.0001        | -               |
| 2.5324 | 6250 | 0.0001        | -               |
| 2.5527 | 6300 | 0.0001        | -               |
| 2.5729 | 6350 | 0.0001        | -               |
| 2.5932 | 6400 | 0.0001        | -               |
| 2.6135 | 6450 | 0.0001        | -               |
| 2.6337 | 6500 | 0.0001        | -               |
| 2.6540 | 6550 | 0.0001        | -               |
| 2.6742 | 6600 | 0.0001        | -               |
| 2.6945 | 6650 | 0.0001        | -               |
| 2.7147 | 6700 | 0.0001        | -               |
| 2.7350 | 6750 | 0.0001        | -               |
| 2.7553 | 6800 | 0.001         | -               |
| 2.7755 | 6850 | 0.0001        | -               |
| 2.7958 | 6900 | 0.0001        | -               |
| 2.8160 | 6950 | 0.0001        | -               |
| 2.8363 | 7000 | 0.0001        | -               |
| 2.8566 | 7050 | 0.0001        | -               |
| 2.8768 | 7100 | 0.0001        | -               |
| 2.8971 | 7150 | 0.0001        | -               |
| 2.9173 | 7200 | 0.0001        | -               |
| 2.9376 | 7250 | 0.0001        | -               |
| 2.9579 | 7300 | 0.0001        | -               |
| 2.9781 | 7350 | 0.0001        | -               |
| 2.9984 | 7400 | 0.0001        | -               |
| 3.0    | 7404 | -             | 0.0000          |

### Framework Versions
- Python: 3.10.0
- SetFit: 1.1.3
- Sentence Transformers: 3.4.1
- Transformers: 4.41.2
- PyTorch: 2.10.0+cpu
- Datasets: 4.6.1
- Tokenizers: 0.19.1

## Citation

### BibTeX
```bibtex
@article{https://doi.org/10.48550/arxiv.2209.11055,
    doi = {10.48550/ARXIV.2209.11055},
    url = {https://arxiv.org/abs/2209.11055},
    author = {Tunstall, Lewis and Reimers, Nils and Jo, Unso Eun Seo and Bates, Luke and Korat, Daniel and Wasserblat, Moshe and Pereg, Oren},
    keywords = {Computation and Language (cs.CL), FOS: Computer and information sciences, FOS: Computer and information sciences},
    title = {Efficient Few-Shot Learning Without Prompts},
    publisher = {arXiv},
    year = {2022},
    copyright = {Creative Commons Attribution 4.0 International}
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->