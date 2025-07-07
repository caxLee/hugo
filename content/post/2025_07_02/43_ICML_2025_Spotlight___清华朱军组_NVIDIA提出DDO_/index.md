+++
date = '2025-07-02T16:36:48+08:00'
draft = false
title = 'ICML 2025 Spotlight | 清华朱军组&NVIDIA提出DDO：扩散/自回归模型训练新范式，刷新图像生成SOTA'
+++

摘要：清华大学博士生郑凯文提出了一种新的视觉生成模型优化方法——直接判别优化（DDO），通过将基于似然的生成模型隐式参数化为GAN，解决了传统最大似然训练的性能瓶颈。DDO不需额外网络、训练高效，提高了生成质量。该方法在多个标准图像生成任务中刷新了现有SOTA。

主题标签：人工智能、深度学习、计算机视觉

## 原文摘要

文章一作郑凯文为清华大学三年级博士生，研究方向为深度生成模型，曾提出流式扩散模型最大似然估计改进技术 i-DODE，扩散模型高效采样器 DPM-Solver-v3，扩散桥模型采样器 DBIM 以及掩码式离散扩散模型采样器 FHS 等。
清华大学朱军教授团队与 NVIDIA Deep Imagination 研究组联合提出一种全新的视觉生成模型优化范式 —— 直接判别优化（DDO）。该方法将基于似然的生成模型（如扩散模型、自回归模型）隐式参数化为 GAN，从而设计出一种无需额外网络、训练高效的微调方法，并大幅突破传统最大似然训练的性能瓶颈。
论文标题：Direct Discriminative Optimization: Your Likelihood-Based Visual Generative Model is Secretly a GAN Discriminator
论文链接：https://arxiv.org/abs/2503.01103
代码仓库：https://github.com/NVlabs/DDO
背景 | 基于似然的生成模型
近年来，扩散模型（Diffusion M...

