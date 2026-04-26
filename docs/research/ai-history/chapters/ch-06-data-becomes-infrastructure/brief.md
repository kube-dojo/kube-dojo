# Chapter 6: Data Becomes Infrastructure (ImageNet)

## Thesis
The deep learning revolution was ignited not by a sudden algorithmic breakthrough, but by the transformation of data into a massively scaled, systematically curated infrastructure. ImageNet proved that in the era of statistical machine learning, the dataset itself was the critical piece of computing infrastructure, shifting the bottleneck from human-engineered rules to massive data collection and labeling pipelines.

## Scope
- IN SCOPE: Fei-Fei Li's conceptualization of ImageNet, the limitations of prior datasets (PASCAL VOC), the leveraging of Amazon Mechanical Turk as human computational infrastructure, the release of the dataset, and the realization that massive datasets were required to train deep neural networks.
- OUT OF SCOPE: The GPU implementation of AlexNet (belongs to Chapter 7); earlier statistical methods (belongs to Chapter 5).

## Scenes Outline
1. **The Algorithm Bottleneck (2006-2007):** Fei-Fei Li's frustration with the plateau in computer vision performance. The realization that better algorithms on small datasets (like PASCAL VOC, which had tens of thousands of images) were hitting a wall, and that capturing the physical world's complexity required unprecedented data scale mapping to WordNet.
   - *Sources:* PASCAL VOC Retrospective (Everingham et al., 2010), Li (2023), Metz (2021).
2. **Mechanical Turk as Infrastructure (2007-2009):** The daunting task of labeling millions of images. Traditional methods (undergraduate lab workers) failed to scale. The crucial pivot to using Amazon Mechanical Turk (launched 2005) as a novel infrastructure for distributed human intelligence, turning a centuries-long task into a manageable engineering pipeline of 24/7 labor.
   - *Sources:* Sorokin & Forsyth (2008), Deng et al. (2009), Quartz (2017).
3. **The ImageNet Release (2009):** The CVPR 2009 poster session where ImageNet was introduced. The academic community, which still heavily favored algorithmic elegance over brute-force data scale, was largely skeptical. ImageNet quietly established the new infrastructural foundation for the coming deep learning boom.
   - *Sources:* Deng et al. (2009), Li (2023), Quartz (2017).
