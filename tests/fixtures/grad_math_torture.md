---
title: "Graduate Math Torture Test"
model: "Ankdown Grad"
tags: [grad-math, torture-test]
---

# Topology & Category Theory

- **Spectral Sequence (Serre)**
    - For a fibration $F \to E \to B$, the $E_2$ page is:
    - $$E_2^{p,q} = H^p(B; H^q(F; G)) \implies H^{p+q}(E; G)$$
    - Differentials $d_r: E_r^{p,q} \to E_r^{p+r, q-r+1}$.
- **Mayer-Vietoris Sequence**
    - For $X = A \cup B$, the long exact sequence in homology is:
    - \begin{tikzcd}
      \dots \to H_n(A \cap B) \to H_n(A) \oplus H_n(B) \to H_n(X) \arrow[dll] \\
      H_{n-1}(A \cap B) \to \dots
      \end{tikzcd}
- **Yoneda Lemma**
    - For a category $\mathcal{C}$ and $F: \mathcal{C} \to \text{Set}$:
    - $$ \text{Nat}(h_A, F) \cong F(A) $$
    - where $h_A = \text{Hom}(A, \cdot)$.

# Differential Geometry

- **Riemann Curvature Tensor**
    - Defined via the connection $\nabla$:
    - $$ R(X,Y)Z = \nabla_X \nabla_Y Z - \nabla_Y \nabla_X Z - \nabla_{[X,Y]} Z $$
    - In components: $R^\rho{}_{\sigma\mu\nu} = \partial_\mu \Gamma^\rho_{\nu\sigma} - \dots$
- **Geodesic Equation**
    - A curve $\gamma$ is a geodesic if $\nabla_{\dot{\gamma}} \dot{\gamma} = 0$.
    - In local coordinates:
    - $$ \frac{d^2 x^\mu}{ds^2} + \Gamma^\mu_{\nu\rho} \frac{dx^\nu}{ds} \frac{dx^\rho}{ds} = 0 $$

# Algebra & Operator Theory

- **Tensor Product Adjunction**
    - $$ \text{Hom}_R(M \otimes_R N, P) \cong \text{Hom}_R(M, \text{Hom}_R(N, P)) $$
- **GNS Construction**
    - State $\omega$ on $C^*$-algebra $\mathcal{A}$:
    - $$ \omega(a) = \langle \xi_\omega, \pi_\omega(a) \xi_\omega \rangle $$
- **Lie Algebra Jacobi Identity**
    - For $x,y,z \in \mathfrak{g}$:
    - $$ [[x,y],z] + [[y,z],x] + [[z,x],y] = 0 $$

# Analysis & Probability

- **Itô's Lemma**
    - $$ df(X_t) = \left( \frac{\partial f}{\partial x} \mu_t + \frac{\partial f}{\partial t} + \frac{1}{2} \frac{\partial^2 f}{\partial x^2} \sigma_t^2 \right) dt + \frac{\partial f}{\partial x} \sigma_t dW_t $$
- **Radon-Nikodym Theorem**
    - For $\nu \ll \mu$, there exists $f \in L^1(\mu)$ such that:
    - $$ \nu(A) = \int_A f \, d\mu $$
    - Denoted as $f = \frac{d\nu}{d\mu}$.

# Whitespace & Formatting Torture

- **Card with extra newlines**


    - This back has extra lines before it.


    - And after it.


- **Card with varying indentation**
  -   Level 2 with 2 spaces
      -   Level 3 with 6 spaces
    -   Back to 4 spaces
- **Equation Spacing Torture**
    - $$
      \begin{aligned}
        \nabla \cdot \mathbf{E} &= \frac{\rho}{\epsilon_0} \\
        \nabla \cdot \mathbf{B} &= 0 \\
        \nabla \times \mathbf{E} &= -\frac{\partial \mathbf{B}}{\partial t} \\
        \nabla \times \mathbf{B} &= \mu_0 \mathbf{J} + \mu_0 \epsilon_0 \frac{\partial \mathbf{E}}{\partial t}
      \end{aligned}
      $$
    - This is Maxwell's equations in an aligned environment with indentation.
- **Mixed List Styles**
    * Homology groups:
      1. $H_0(X)$
      2. $H_n(X)$ for $n > 0$
         - Check coefficients in $\mathbb{Z}, \mathbb{Q}, \mathbb{R}$.

# Media & Image Torture

- **Image with relative path**
    - This card contains a logo from a subfolder:
    - ![Logo](sub/logo.png)
    - It should be mangled to `sub%logo.png`.

- **Legacy Macro Check: Number Sets**
    - The set of real numbers is $\RR$.
    - The set of natural numbers is $\NN$.
    - The complex numbers $\CC$ satisfy $\CC \cong \RR^2$ as real vector spaces.
- **Legacy Macro Check: Lie Algebras**
    - The Lie algebra of $G$ is denoted $\lieg$.
    - A Borel subalgebra is $\lieb \subset \lieg$.
- **Legacy Macro Check: Delimiters**
    - Define the set $\theset{x \in \RR \suchthat x^2 = 2}$.
    - Note the use of `\suchthat` and `\RR`.
