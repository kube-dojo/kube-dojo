# Infrastructure Log: Chapter 38 - The Human API

## Scene 1: Catalog Problem and Hybrid Machine/Human Computing

- **Problem substrate:** Amazon's growing product catalog, where secondary sources report duplicate listings across product pages.
- **Machine limitation:** Duplicate detection required image/text similarity judgments that were difficult for conventional software, per IEEE Spectrum's secondary account.
- **Architecture anchor:** US7197459B1 describes a central coordinating server, human-operated nodes, a task server, and a "Junta Computer" that receives decomposed subtasks.
- **API parameters:** The patent's API can encode task nature, input data, expected accuracy, security level, maximum subtask time, and cost.
- **Evidence limits:** The patent is general; the duplicate-catalog use case is secondary-anchored and should be framed as reported origin, not as patent text.

## Scene 2: Public MTurk Launch

- **Service layer:** AWS announces MTurk as a web-services API on November 2, 2005.
- **Human/computer inversion:** Instead of a human asking a computer to complete a task, a computer program can ask humans and receive results.
- **Named abstraction:** "Artificial Artificial Intelligence" is primary-anchored in the AWS announcement.
- **Task type anchor:** AWS uses identifying objects in photographs as the public example of human strength over computers.

## Scene 3: AWS Delivery Vehicle

- **Developer platform:** Computerworld reports roughly 200,000 developers registered for 10 Amazon web services by September 2006.
- **Sibling services:** MTurk appears alongside S3 and EC2 in Bezos's MIT keynote, which matters because human labor was being packaged in the same developer-service vocabulary as storage and compute.
- **Business model:** "Pay-by-drink" and small bills show metering and experimentation as infrastructure features.
- **Internal-to-external pattern:** Bezos's reported claim that Amazon exposed things it already had to do internally supports the chapter's infrastructure thesis.

## Scene 4: NLP Annotation Pipeline

- **Requester workflow:** Snow et al. describe HIT groups, requested annotations per HIT, reward payment, qualifications, worker choice, approval, bonus, and Amazon-mediated financial transactions.
- **Quality method:** Ten independent annotations per item create redundancy; aggregation and bias correction improve reliability.
- **Cost anchor:** Affect recognition labels: $2 for 7,000 non-expert annotations; interpreted as 3,500 labels per USD and at least 875 expert-equivalent labels per USD.
- **Caution:** Snow et al. validate specific task designs. The prose must not generalize their result to all annotation or all workers.

## Scene 5: ImageNet and Hidden Labor

- **Candidate-image pipeline:** ImageNet uses WordNet synsets, web image search, query expansion, and multilingual translation to build large candidate pools.
- **AMT cleaning:** Human workers verify whether candidate images contain objects of the target synset.
- **Quality control:** Multiple independent labels, initial subsets with at least ten votes, confidence score tables, and thresholds for continuing or stopping labeling.
- **Scale:** 2009 state: 12 subtrees, 5,247 synsets, 3.2 million images; target: tens of millions of clean full-resolution images.
- **Labor boundary:** Hara et al. later measure 2,676 workers and 3.8 million HITs, finding low median hourly wages and unpaid search/rejection/non-submission time. Use this to close the chapter honestly, not to retroactively quantify 2005-2009 wages.
