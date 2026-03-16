---
tags:
- setfit
- sentence-transformers
- text-classification
- generated_from_setfit_trainer
widget:
- text: find buyers for calcium carbonate
- text: sourcing dextrose anhydrous
- text: shipments of lactose to Reckitt Benckiser
- text: country comparison for sodium chloride
- text: best markets for lactose
metrics:
- accuracy
pipeline_tag: text-classification
library_name: setfit
inference: true
base_model: sentence-transformers/all-mpnet-base-v2
model-index:
- name: SetFit with sentence-transformers/all-mpnet-base-v2
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
      value: 0.9846153846153847
      name: Accuracy
---

# SetFit with sentence-transformers/all-mpnet-base-v2

This is a [SetFit](https://github.com/huggingface/setfit) model that can be used for Text Classification. This SetFit model uses [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) as the Sentence Transformer embedding model. A [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) instance is used for classification.

The model has been trained using an efficient few-shot learning technique that involves:

1. Fine-tuning a [Sentence Transformer](https://www.sbert.net) with contrastive learning.
2. Training a classification head with features from the fine-tuned Sentence Transformer.

## Model Details

### Model Description
- **Model Type:** SetFit
- **Sentence Transformer body:** [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)
- **Classification head:** a [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) instance
- **Maximum Sequence Length:** 384 tokens
- **Number of Classes:** 8 classes
<!-- - **Training Dataset:** [Unknown](https://huggingface.co/datasets/unknown) -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Repository:** [SetFit on GitHub](https://github.com/huggingface/setfit)
- **Paper:** [Efficient Few-Shot Learning Without Prompts](https://arxiv.org/abs/2209.11055)
- **Blogpost:** [SetFit: Efficient Few-Shot Learning Without Prompts](https://huggingface.co/blog/setfit)

### Model Labels
| Label       | Examples                                                                                                                                                    |
|:------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------|
| BUY         | <ul><li>'dextrose suppliers please'</li><li>'looking for wheat suppliers'</li><li>'where can I buy glucose syrup'</li></ul>                                 |
| SELL        | <ul><li>'buyers for our sodium chloride'</li><li>'I want to sell my dextrose'</li><li>'buyers for our citric acid'</li></ul>                                |
| F6_TOPK     | <ul><li>'suggest 5 best glucose importers'</li><li>'top suppliers of lactose'</li><li>'top 5 dextrose anhydrous suppliers'</li></ul>                        |
| F7_COMPARE  | <ul><li>'best export destinations for dextrose'</li><li>'best country for selling soy lecithin'</li><li>'import breakdown by country for glucose'</li></ul> |
| F8_EVIDENCE | <ul><li>'did Quaker Oats buy wheat starch'</li><li>'shipments received by Muller Phipps'</li><li>'has Nestle imported dextrose anhydrous'</li></ul>         |
| F3_VOLUME   | <ul><li>'3000 MT sugar cane supplier'</li><li>'supply 450 metric tons starch'</li><li>'I need 100 MT starch'</li></ul>                                      |
| F4_PRICE    | <ul><li>'sorbitol above $400 per ton'</li><li>'tapioca starch below $180 per MT'</li><li>'best priced tapioca starch below $200'</li></ul>                  |
| F5_TIME     | <ul><li>'last 6 months sorbitol suppliers'</li><li>'Q3 2024 sugar exporters'</li><li>'last year citric acid imports'</li></ul>                              |

## Evaluation

### Metrics
| Label   | Accuracy |
|:--------|:---------|
| **all** | 0.9846   |

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
preds = model("best markets for lactose")
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
| Word count   | 2   | 5.0934 | 9   |

| Label       | Training Sample Count |
|:------------|:----------------------|
| BUY         | 32                    |
| F3_VOLUME   | 32                    |
| F4_PRICE    | 32                    |
| F5_TIME     | 32                    |
| F6_TOPK     | 32                    |
| F7_COMPARE  | 32                    |
| F8_EVIDENCE | 32                    |
| SELL        | 33                    |

### Training Hyperparameters
- batch_size: (16, 16)
- num_epochs: (1, 1)
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
- eval_max_steps: -1
- load_best_model_at_end: False

### Training Results
| Epoch  | Step | Training Loss | Validation Loss |
|:------:|:----:|:-------------:|:---------------:|
| 0.0003 | 1    | 0.2374        | -               |
| 0.0138 | 50   | 0.2238        | -               |
| 0.0277 | 100  | 0.1688        | -               |
| 0.0415 | 150  | 0.0882        | -               |
| 0.0554 | 200  | 0.0365        | -               |
| 0.0692 | 250  | 0.0115        | -               |
| 0.0831 | 300  | 0.004         | -               |
| 0.0969 | 350  | 0.0024        | -               |
| 0.1107 | 400  | 0.0016        | -               |
| 0.1246 | 450  | 0.0013        | -               |
| 0.1384 | 500  | 0.001         | -               |
| 0.1523 | 550  | 0.0009        | -               |
| 0.1661 | 600  | 0.0007        | -               |
| 0.1800 | 650  | 0.0006        | -               |
| 0.1938 | 700  | 0.0006        | -               |
| 0.2076 | 750  | 0.0006        | -               |
| 0.2215 | 800  | 0.0005        | -               |
| 0.2353 | 850  | 0.0004        | -               |
| 0.2492 | 900  | 0.0004        | -               |
| 0.2630 | 950  | 0.0004        | -               |
| 0.2769 | 1000 | 0.0004        | -               |
| 0.2907 | 1050 | 0.0004        | -               |
| 0.3045 | 1100 | 0.0003        | -               |
| 0.3184 | 1150 | 0.0003        | -               |
| 0.3322 | 1200 | 0.0003        | -               |
| 0.3461 | 1250 | 0.0003        | -               |
| 0.3599 | 1300 | 0.0003        | -               |
| 0.3738 | 1350 | 0.0003        | -               |
| 0.3876 | 1400 | 0.0003        | -               |
| 0.4014 | 1450 | 0.0003        | -               |
| 0.4153 | 1500 | 0.0003        | -               |
| 0.4291 | 1550 | 0.0003        | -               |
| 0.4430 | 1600 | 0.0002        | -               |
| 0.4568 | 1650 | 0.0002        | -               |
| 0.4707 | 1700 | 0.0002        | -               |
| 0.4845 | 1750 | 0.0002        | -               |
| 0.4983 | 1800 | 0.0002        | -               |
| 0.5122 | 1850 | 0.0002        | -               |
| 0.5260 | 1900 | 0.0002        | -               |
| 0.5399 | 1950 | 0.0002        | -               |
| 0.5537 | 2000 | 0.0002        | -               |
| 0.5676 | 2050 | 0.0002        | -               |
| 0.5814 | 2100 | 0.0002        | -               |
| 0.5952 | 2150 | 0.0002        | -               |
| 0.6091 | 2200 | 0.0002        | -               |
| 0.6229 | 2250 | 0.0002        | -               |
| 0.6368 | 2300 | 0.0002        | -               |
| 0.6506 | 2350 | 0.0002        | -               |
| 0.6645 | 2400 | 0.0002        | -               |
| 0.6783 | 2450 | 0.0002        | -               |
| 0.6921 | 2500 | 0.0002        | -               |
| 0.7060 | 2550 | 0.0002        | -               |
| 0.7198 | 2600 | 0.0002        | -               |
| 0.7337 | 2650 | 0.0002        | -               |
| 0.7475 | 2700 | 0.0002        | -               |
| 0.7614 | 2750 | 0.0002        | -               |
| 0.7752 | 2800 | 0.0002        | -               |
| 0.7890 | 2850 | 0.0002        | -               |
| 0.8029 | 2900 | 0.0002        | -               |
| 0.8167 | 2950 | 0.0002        | -               |
| 0.8306 | 3000 | 0.0002        | -               |
| 0.8444 | 3050 | 0.0002        | -               |
| 0.8583 | 3100 | 0.0002        | -               |
| 0.8721 | 3150 | 0.0002        | -               |
| 0.8859 | 3200 | 0.0002        | -               |
| 0.8998 | 3250 | 0.0002        | -               |
| 0.9136 | 3300 | 0.0002        | -               |
| 0.9275 | 3350 | 0.0002        | -               |
| 0.9413 | 3400 | 0.0002        | -               |
| 0.9551 | 3450 | 0.0002        | -               |
| 0.9690 | 3500 | 0.0001        | -               |
| 0.9828 | 3550 | 0.0002        | -               |
| 0.9967 | 3600 | 0.0001        | -               |

### Framework Versions
- Python: 3.12.3
- SetFit: 1.1.3
- Sentence Transformers: 5.2.2
- Transformers: 4.57.3
- PyTorch: 2.8.0+cu128
- Datasets: 4.4.1
- Tokenizers: 0.22.1

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