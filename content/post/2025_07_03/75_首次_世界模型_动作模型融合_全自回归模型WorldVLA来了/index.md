+++
date = '2025-07-03T21:53:09+08:00'
draft = false
title = '首次！世界模型、动作模型融合，全自回归模型WorldVLA来了'
+++

摘要：阿里巴巴达摩院研究员岑俊提出了WorldVLA模型，将世界模型和动作模型融合，实现了统一的文本、图片、动作理解和生成模型。该模型通过自回归机制实现双向图像与动作的理解和生成，采用动作注意力掩码策略解决了动作累积误差问题，在实验中表现出良好的性能。

主题标签：人工智能、机器学习、模型融合

## 原文摘要

岑俊，阿里巴巴达摩院具身智能大模型算法研究员，博士毕业于香港科技大学。研究方向主要是：具身智能 VLA 模型，世界模型。
阿里巴巴达摩院提出了 WorldVLA, 首次将世界模型 (World Model) 和动作模型 (Action Model/VLA Model) 融合到了一个模型中。WorldVLA 是一个统一了文本、图片、动作理解和生成的全自回归模型。
论文标题：WorldVLA: Towards Autoregressive Action World Model
论文地址：https://arxiv.org/pdf/2506.21539
代码地址：https://github.com/alibaba-damo-academy/WorldVLA
研究简介
近年来，视觉 - 语言 - 动作（Vision-Language-Action, VLA）模型的发展成为机器人动作建模研究的重要方向。这类模型通常是在大规模预训练的多模态大语言模型（Multimodal Large Language Models, MLLMs）基础上，添加一个动作输出头或专门的动作模块，以实现对动作的生成。M...

