# On the Temporal Relations between Logging and Code

This repo contains the data and the source code of  the tool (i.e., **TempoLo**) used in our paper *On the Temporal Relations between Logging and Code*. 

The `data` folder contains the data files used in our paper and the jupyter contains the jupyter notebooks for reproducing the results. Two files `tempolo_semantic.py` and `inconsistency_detection.py` are the two source files that implemented the rules and findings from our paper. The file `config.json` is used for keeping the info of the database connections.

## Requirements and Installation

* Python version == 3.6
* Postgresql
* srcML
* Refer to `spec-file.txt` for the dependent library


## Data description

The data can be found in the `data` directory, which contains six files: 

* `all_local_string.pkl`: the file cotnains all the extracted local strings from Tomcat project, which is used dring the extraction of the logging text. 
* `sampled_logs.csv`: the file contains the sampled log statements extract from four projects.
* `ground_truth.csv`: the file contains the manually identified temporal inconsistencies from the sampled data, which is used as our first evaluation data
* `detected-log-code-inconsistency.csv`: the file contains the detected temporal inconsistencies from the remaining data, which is used as our second evaluation data
* `commit-history.csv`: the file contains the temporal inconsistencies mined from commit history, which is used as our third evaluation data.
* `tempolo.sql.zip`: the file is split into two parts and contains all the extracted logging statements as well as the methods from the four projects.

## Replicate the results
> 1. Create an empty database named **logs** using PostgreSQL.

> 2. Unzip the file **tempolo.sql.zip.001** (we split the original zip file, **tempolo.sql.zip** into two parts, and they should be put together and then unzip the first part **tempolo.sql.zip.001**), and then restore it to the DB: **logs** using command **pg_restore**.

> 3. Modify the configuration file: **config.json** with your own database information.

> 4. Change the directory to the **jupyter**, and run the following command:
```
jupyter notebook
```

> 5. The notebook file **Replication-Package.ipynb** contains all the source code for reproducing the results reported in our paper.

## Discussion on a machine learning-based approach. 
Besides the rule-based approach, we also implemented another machine-learning (ML) based approach to locate the target source code, aiming to reduce the efforts of refining the rules. 

We first extract three types of features: (1) considering the logging statement and source code as plain text and utilizing the features that are widely used in NLP, such as string similarity, entropy, and tf-idf; (2) distances (e.g., line distance, AST node distance, and block distance) between the logging statement and each line of source code; (3) using the newly released CodeBERT model [29] to generate distributed representations of the logging statement and the source code. Then, we adopt the LambdaRank model [30] to perform the pairwise ranking. 

We evaluate the accuracy of the ML based approach by manually labeling around 600 logging statements and their corresponding source code. We split 80% of the dataset as training and the remaining 20% for testing. As a result, the ML based approach only returns a top-1 accuracy of 50%. Besides, there may exist deep learning models that are useful for aligning code and natural language in other tasks [31], but they often require a larger labeled dataset. Considering the low accuracy and the costly labeling efforts, we opt to not use the ML (or DL) based approach.

## Discussion on potential downstream tasks.

Some downstream tasks may potentially benefit from utilizing our observations of the logging-code temporal relations and our tool. For example, in the task of automatic logging text generation, we ﬁnd that although LoGenText proposed by Ding et al. [10] produces SOTA results, there still exist cases that can be improved by fixing the temporal inconsistencies ([Result Link](https://github.com/conf-202x/experimental-result)). For example, as shown below, developers insert two logging statements (line 2 and line 5) to describe different status of the “close()” statement (line 4). In this task, the ﬁrst logging statement (line 2) is masked, and based on the given source code, LoGenText generates the perfective word “closed” (instead of the word “closing” used by developer), which violates the intention of the developer. Future work may consider using our tool to detect such inconsistencies and improve the results. 

Besides, by considering the temporal relationship, prior studies (e.g., [32]) that build ﬁnite state machines from logs can more accurately represent the actual temporal status of the events described in the logs.

```
...
1 // Generated logging text by LoGenText: LOG.debug("closed socket {}")
2 LOG.debug("closing socket {}")
3 try {
4     socket.close();
5     LOG.debug("Closed socket {}", socket);
...
```
### References

[10] Z. Ding, H. Li, and W. Shang, “Logentext: Automatically generating logging texts using neural machine translation,” in Proceedings of the 29th IEEE International Conference on Software Analysis, Evolution and Reengineering, ser. SANER ’22, 2022.

[29] Z. Feng, D. Guo, D. Tang, N. Duan, X. Feng, M. Gong, L. Shou, B. Qin, T. Liu, D. Jiang, and M. Zhou, “Codebert: A pre-trained model for programming and natural languages,” in Findings of the Association for Computational Linguistics: EMNLP 2020, Online Event, 16-20 November 2020, ser. Findings of ACL, T. Cohn, Y. He, and Y. Liu, Eds., vol. EMNLP 2020. Association for Computational Linguistics, 2020, pp. 1536–1547.

[30] C. J. C. Burges, R. Ragno, and Q. V. Le, “Learning to rank with non-smooth cost functions,” in Advances in Neural Information Processing Systems 19, Proceedings of the Twentieth Annual Conference on Neural Information Processing Systems, Vancouver, British Columbia, Canada, December 4-7, 2006, B. Schölkopf, J. C. Platt, and T. Hofmann, Eds. MIT Press, 2006, pp. 193–200.

[31] Z. Liu, X. Xia, M. Yan, and S. Li, “Automating just-in-time comment updating,” in Proceedings of the 35th IEEE/ACM International Conference on Automated Software Engineering, ser. ASE ’20. New York, NY, USA: Association for Computing Machinery, 2020, p. 585–597. [Online]. Available: https://doi.org/10.1145/3324884.3416581
