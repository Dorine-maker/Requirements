
# Protocole Expérimental – Analyse des Exigences Fonctionnelles avec LLMs

## 1. Objectif

Ce projet étudie les capacités des LLM à extraire des **exigences fonctionnelles testables** à partir d’un cahier des charges, puis à évaluer la conformité de ces exigences par d’autres LLM.

---

## 2. Prompt du cahier des charges
Do not take previous responses into account.
You are a Software Testing Specialist with expertise in analyzing project specifications and deriving functional testing requirements. Your goal is to ensure that all functional aspects of the system are thoroughly tested.

Instructions:

Carefully analyze the provided project specifications. Extract only functional testing requirements from the specifications. Ensure that each requirement is specific, measurable, and testable. Do not include non-functional requirements (e.g., performance, security) or test cases. Use clear and concise language.

Constraints:

Focus exclusively on functional aspects of the system. Do not add explanations, assumptions, or additional context. Ensure that each requirement is independent and does not overlap with others. If the specifications are ambiguous, make reasonable assumptions but keep the requirements aligned with typical functional testing practices.

Format:

List the requirements by starting each one in a new line. Exemple of format for requirement : The $<$role$>$ can $<$functionality$>$

Project Specifications:

Description

The www.kiestla.edu website aims to simplify the management of student attendance control during classes. The site is a portal linking students, teachers and administrative staff. The site handles the entire process, from recording an absence to justifying it to the administration.

Functionalities

The site has an administrator who manages the creation, maintenance and deletion of teaching modules and their association with one or more referent teachers. Teachers and students are grouped together in a global database also managed by the administrator. The referent teacher can add teachers and students if they are already registered in the database. When a teacher reports an absence in a module, they can add a comment. A teacher can consult the list of absences for all students enrolled in one of their modules. The administrative staff then enters the reason for the absence and has access to all student absences. Absences can be grouped by module and by student. In addition, a page alerts teaching staff to students with more than 3 unjustified absences.

---

## 4. Déroulement expérimental

1. Le cahier des charges est donné **10 fois** à 5 LLM :

   * ChatGPT (GPT-5-mini)
   * DeepSeek V3
   * Mistral AI (version avril 2026)
   * Qwen3.6-Plus
   * Claude Sonnet 4.6
2. Chaque LLM produit un fichier `<nom_du_LLM>Req.txt` contenant :

   * La ligne de **spécification rappelée**
   * Les exigences associées aux tests (T1, T2, …)
3. **Évaluation par d’autres LLM :**

   * Script d’analyse (à ne pas modifier) :

     ```
     Analyze requirements with respect to a specification document and classify it into one of the following categories:

     1-It complies with the specification
     2-It highlights missing information
     3-It provides a useful or relevant improvement
     4-It introduces something unnecessary or contradicts the specification

     Specification : <Nom de la specification>

     Requirements :
     <Nom de l'exigence>
     ```
   * Exemple :

     ```
     Specification : Teachers and students are grouped together in a global database also managed by the administrator.

     Requirements :
     The administrator can manage a global database of teachers
     The administrator can manage a global database of students
     ```
4. **Résultat des évaluations :**

   * Fichier généré :

     ```
     Req_<nomDuLLM1>_Evaluateur<nomDuLLM2>.txt
     ```
   * Chaque exigence est classée selon le code 1 à 4 :

     * Si classification = 1 : pas de commentaire ajouté.
     * Sinon : le commentaire de l’évaluateur est ajouté sous l’exigence.

---

## 5. Structure des fichiers

* `<nom_du_LLM>Req.txt` : exigences extraites par le LLM.
* `Req_<nomDuLLM1>_Evaluateur<nomDuLLM2>.txt` : évaluation des exigences du LLM1 par le LLM2.
* Chaque exigence est précédée de la ligne de spécification correspondante.
* Les tests sont identifiés (T1, T2…) pour la traçabilité.

---

## 6. Objectifs scientifiques

* Évaluer la capacité des LLM à extraire des exigences fonctionnelles précises et testables.
* Mesurer la cohérence et la conformité des exigences par d’autres LLM.
* Identifier les écarts, améliorations ou contradictions dans l’analyse des exigences.

