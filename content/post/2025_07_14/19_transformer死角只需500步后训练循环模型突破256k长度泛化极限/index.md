+++
title = 'Transformer死角，只需500步后训练，循环模型突破256k长度泛化极限'
date = "2025-07-14T21:13:58.709394+08:00"
draft = false
tags = ["\u957f\u5ea6\u6cdb\u5316", "\u8bad\u7ec3\u5e72\u9884", "\u6709\u6548\u8bb0\u5fc6"]
summary = "循环模型在处理长序列时无法实现长度泛化，因为模型在训练过程中未能接触到超出训练长度范围的状态，导致性能下降。研究者通过训练干预的方法，成功实现了循环模型在长序列上的泛化能力，展现了循环模型潜在的性能提升。同时，通过有效记忆的度量，研究者深入探讨了模型如何处理上下文的行为。"
slug = "transformer死角只需500步后训练循环模型突破256k长度泛化极限"
link = "https://www.jiqizhixin.com/articles/2025-07-08-7"
+++

循环模型在处理长序列时无法实现长度泛化，因为模型在训练过程中未能接触到超出训练长度范围的状态，导致性能下降。研究者通过训练干预的方法，成功实现了循环模型在长序列上的泛化能力，展现了循环模型潜在的性能提升。同时，通过有效记忆的度量，研究者深入探讨了模型如何处理上下文的行为。

<!--more-->
