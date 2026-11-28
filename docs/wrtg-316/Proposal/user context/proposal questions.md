# Proposal questions

Short answers are fine: a phrase, a few bullets or "don't know yet." Write each answer under
its question, after the `>`. Where I already have something from earlier sessions, it's under
**Current guess**: confirm it or correct it.

The sections follow the assignment's required headings in order. The checklist at the end maps
every requirement in the assignment to the questions that cover it.

Also, we will review this document when it is time to begin the paper itself.

---

## 0. Big picture

**0.1 Title.** The proposal needs a well-thought-out title.
Current guess: *When Is a Low-Cost Arm Good Enough?* Keep it, change it, or add a subtitle?
>During the steering session lets come back to this one. I think we can modify the title after weve populated the proposal. Since this is a proposal, make "Research Paper Proposal" the subtitle. I think the title could be something like "Comparing Low-Cost Robot Arms to Industry Standards" or "When Is a Low-Cost Arm Good Enough? ... whatever else was in the title before I made that change" idk something good, descriptive, but consise. 

**0.2 Empirical work.** The report must be empirical. Will you run your own tests on the PiPER
(or the SO-101 arms) and report the data, or rely on published measurements, or both? If your
own tests, which ones (e.g., repeatability, pick-and-place success rate, payload)?
>Not right now. The origional plan was to run my own tests to compare with industry standard. However, the focus of the paper has shifted to discovering the tests that determine the value of a robot arm in an SDL. In otherwords, discovering the very tests we will eventually run with our PiPER and SO-101 arms. 

**0.3 Report length check.** The report body is about 10 pages. What would you cut first if
the topic proves too big?
>come back to this later

**0.4 Audience.** Who is the report written for (e.g., lab managers choosing an arm, robotics
researchers, the course instructor as a general technical reader)? What do they already know?
>Proposal the ONLY AUDIENCE IS MY PROFESSOR - he made that clear. For the paper it is robotics researchers, BUT we want to focus on clarity. In the private folder of this repo, there is a folder called IMRad. Read through that document looking for the relevant section to describe the reading level the reader should expect. Either way, the audience is researchers but undergraduate level researchers. The writing style should be clear, never pretentious. That said reason can be complex, but always thorough. 

**0.5 Citation style.** Current guess: IEEE. Confirm?
>yes. You will also need to get a photo copy or direct copy of some sort of IEEE formating rubric for citations and bibliography with an example. These should be the very last pages in the paper. 

**0.6 Graphics.** Do you want any figures or tables in the proposal (e.g., the sandbox render,
a cost comparison table, a timeline chart)? Which ones?
>Ignore EVERYTHING, not just figures, from the test LaTex doc. We will be rewriting this from scratch. Lets write the proposal and then come back to this question. 

**0.7 Due dates.** When is the proposal due, and when is the final report due?
>It was due 11/4/2026. The final report due date is December 1st.

---

## 1. Introduction

**1.1 Opening.** What should the first paragraph make the reader feel or notice? Any hook you
like (a cost figure, a lab anecdote, a failure you saw)?
>A reality check about how automation in laboratories is growing specifically in material and biological sciences

### 1.2 The Research Issue and Its Background

**1.2.1 The issue in one sentence.** What is the problem or debate?
>Which metrics and repeatable testing is used to evaluate repeatability and reliability for robotics and using those tests how useful are low-cost robotics like the PiPER arm (and maybe the SO-101 arms or similar) in SDLs (self-driving labs). That is the real issue for your context. It's probably summarized better as: "What is the best way to analyze a robotic arm setup for SDL use?" OR "How do low-cost robotic arms compare to industrial standards?" OR "Can many industrial workflows me modified so that low-cost robot arms can fulfill the same purpose?" We will need to refine this.

**1.2.2 Why it interests you, and should interest the reader.**
>I've been interested in robotics controls since I was in middle school (on the robotics competition team), high school (leader of the brand new robotics team) and do several projects on the side. I am applying to graduate school and this project will make up a portion of my letter of intent and play a role in my advisor's letter of recommendation. 

**1.2.3 History and context.** What happened that makes this timely? (e.g., arm prices
dropping, self-driving labs growing, open-source arms like SO-101 appearing.) Any dates or
milestones you know?
>refer to 1.1 opening paragraph

**1.2.4 How the literature treats it.** In a sentence or two each: what do researchers say?
What do industry or vendors say? Where do they disagree or leave gaps?
>not sure at the moment. I need you to look into this for now.

### 1.3 Research Questions and Thesis Statement

**1.3.1 Main research question.**
>What tests can we run with our PiPER robot arm that will compare it's value to industry standard arms used as automated manual manipulators in self driving labs? IMPORTANT!! LET ME KNOW IF THIS QUESTION IS ALREADY WRITTEN ABOUT. I WOULD LIKE TO READ SPECIFIC ARTICLES THAT HAVE THIS SAME EXACT PURPOSE.

**1.3.2 Thesis statement.** It must be an argument someone would disagree with. Draft one, even
if rough.
>Help me come up with this. 

**1.3.3 Who would disagree, and why?**
>Not sure. yet

**1.3.4 Narrow enough?** What scope limits keep it to 8 to 10 pages (which tasks, which arms,
which kind of lab)?
>Since refining the scope to test discovery, we will not be analyzing data collected in our lab. Instead we will be focusing only on the literature review of sources on this topic and selecting a list of tests.

**1.3.5 Your curiosity.** What made you curious about this? What experience prompted the
questions?
>Refer to question 1.2.2, but also know that I am applying to graduate school with a professor who's lab is engaged in building an automated Self Driving Lab (SDL) for material science research. I am in leadership in his lab this semseter. 

**1.3.6 The larger question.** What bigger question runs underneath this one (e.g., "can
affordable automation democratize lab research?"), and how does answering your question help
answer it?
>can affordable automation democratize self driving lab research? Our question (refer to question 1.3.1) will give us benchmarking tests to run so the we or someone else can validate their affordable automation solutions.

**1.3.7 Your list of questions.** List every question you have about the subject. For each,
give a short answer if you know it, or write "unknown."
>
> 1. Has anyone written about this before and what did they say? - Unknown
> 2. Are there different categories of robotic arms to consider? - Unknown
> 3. What metrics are used when making decisions to purchase a robot arm to be an automated manual manipulator? - Unknown

### 1.4 Research Subject Justification and Purpose

**1.4.1 So what?** Why should a reader care? What goes wrong if nobody answers this question?
> A reader should care if they are going to be purchasing an automated manual manipulator for a self driving lab or if they are designing a robot arm for sale. If nobody answers this question then scientific consumers will continue to purchase expensive arms when less expensive arms may have been suitable, the barier to entry remains high, and certain benchmarks for testing a robot will go unused. 

**1.4.2 Necessity and relevance.** Who needs the answer right now, and what decision does it
inform?
> refer to 1.4.1

**1.4.3 Your position.** In one sentence, which side do you take?
> Unknown

**1.4.4 Counter-arguments.** List the strongest arguments against your thesis (at least two or
three). For each, a few words on how you'll answer it.
>
> 1. I don't have these yet. 
> 2. ^^
> 3. ^^

**1.4.5 Your unique perspective.** What do you bring that the literature doesn't? (e.g.,
hands-on data from a working lab cell, a student-built testbed, a cost-per-task angle.)
> I am building a lab from scratch, where we have valued the cost-per-task which is often not the priority in expensive RnD. 

**1.4.6 The reader's course of action.** After reading, what should the reader do?
> The reader test their own automated manual manipulators against the benchmarks determined to evaluate the reliability and/or the  repeatability of their arm for the tasks it will be completing. They can also be informed as to which cheaper options are available. 

**1.4.7 Your purpose.** Why are you researching this, beyond the assignment?
> I want benchmarks to perfom testing on the PiPER AgileX and SO-101 Leader/Follower robots that I have. Then with those test results I want to evaluate other arms for purchase in our lab, which decisions will be informed with actual metrics. 

---

## 2. Qualifications for Research on Topic X

**2.0 Heading name.** The "Topic X" in this heading is replaced with your topic. What short
topic name should go there (e.g., "Low-Cost Robot Arms in Self-Driving Labs")?
>

### 2.1 Capability

**2.1.1 Passion.** Why do you care about this topic?
> I am doing robotics research and applying to graduate school for this.

**2.1.2 Experience.** What experience qualifies you? (Your role in the Vertical Cloud Lab, time
with the PiPER, programming, CAD, coursework, anything relevant.)
> I am helping lead a team of lab assistants build a robot arm enclosure, I have done research and product development on data aquisition and mechatronic systems in the past, I am a senior mechanical engineering student. 

**2.1.3 Capabilities needed.** What skills does this research require (e.g., running and
measuring arm tests, statistics, reading robotics papers)? Which do you have, and which will
you build or borrow?
> We will not be gathering data for this paper. This paper will only be a literature review designs to systemmatically scope out benchmarks for testing and evaluate the the grading process for arm purchasing based on required tasks.  

### 2.2 Library Research Skills

**2.2.1 Library mini-course.** Did you attend the library mini-course for your major? When, and
who taught it? Anything from it you'll use?
> I attended the mini-course on Oct 27th, it was taught by a SLC librarian, and I will use the databases and web searching techniques she recommended I use.  

**2.2.2 Subject resources (at least three).** Which databases, specialized encyclopedias,
association websites or similar will you use? For each: what it contains, and why it's useful
for you.
Current guess, from your database-search notes: Scopus, Engineering Village (Compendex +
Inspec), IEEE Xplore. Confirm, add or swap. Possible extras: IEEE Robotics and Automation
Society, ISO 9283 (the standard for measuring robot accuracy and repeatability).
>
> 1. Scopus
> 2. Engineering Village
> 3. IEEE Xplore
> 4. Googel Scholar
> 5. I will use Edison Scientific Queries with Claude which will search for open source resources.

### 2.3 Review of Literature

Two sources, the ones you predict will matter most. Each gets one or two short paragraphs in
the proposal, with its author and title.

**2.3.1 Source A and B.** Author and title, or a link. What does it argue or find? How does it fit
your strategy (support, counter-argument, method to copy)?
> Use the two strongest from the nine picks in docs\wrtg-316\edison\Final_Selection.md



### 2.4 Annotated Bibliography

At least seven sources, **not** including the two above, formatted in your citation style. Each
gets one or two sentences on why it's among the best.

**2.4.1 Your seven (or more).** List them, or say "use the selection.md picks plus the database
search results" and I'll draft the list for you to check.
>
> 1. Populate using docs\wrtg-316\edison\Final_Selection.md

**2.4.2 Gaps.** Any kind of source missing (e.g., a counter-argument source, an industry report,
a standards document)?
>

---

## 3. Research Plan and Methodology

### 3.1 Methods

**3.1.1 What is your research?** One or two sentences.
> You can answer this from context above. 

**3.1.2 How will you conduct it?** Steps: literature search, lab tests, analysis, or anything
else.
> 1. Search data bases for sources (may have been completed at this point)
> 2. Summarize and synthisize results
> 3. Compile a list of benchmark tests
> 4. Write the proposal, review, edit, repeat

**3.1.3 Authorities.** Who or what are the authorities on this subject (researchers, labs,
standards bodies, companies)?
> I don't know, lets scrape the sources to find out.

**3.1.4 Specific places and texts.** Which sites, databases, key texts and authors will be
essential?
> Unknown, see 3.1.3

**3.1.5 Non-text research.** Any fieldwork, interviews, surveys or experiments? (e.g.,
measuring the PiPER in the lab, interviewing your PI or lab members about what accuracy their
tasks need.) Who, and roughly how many?
> Not in this proposal or paper.

**3.1.6 Source biases.** What biases might your sources have (vendor specs written to sell,
papers that only report successes, your own lab's investment in the PiPER)? How will you
account for them?
> The largest source of bias will be my personal bias (as the paper author) leaning towards the idea that affordable robotic arms can serve as useful automated manual maniplulators. This is because I am an undergraduate researcher with limited resources and prior experience with only affordable robotic options. I will account for this bias by reporting all objective facts related to what measures are useful in grading efficiency of an automated manual manipulator to fulfill certain tasks. I will also rely on quantatative, measureable data to support the aurguments I'll make. 

### 3.2 Proposed Outline of Research Report

**3.2.1 Outline.** Sketch the report's sections, or say "draft one for me" and I'll propose
an outline for you to edit.
> draft one for me

### 3.3 Research Timeline

**3.3.1 Milestones.** From start to finish, what milestones and dates? (e.g., sources gathered,
lab tests run, draft, peer review, final.) Or give me the course deadlines and I'll draft a
timeline.
> the dealine for the paper is Dec 1st. draft a timeline. Know that my personal timeline has historically showed that I get 80-90% of the work completed just a few days before the final deadline. I also get large amounts of work done in a large distraction free period of time. Some major milstones for you to draft will be: find sources, draft proposal, review draft and edit to submit final proposal, overhaul paper draft, paper scope modification edit, paper arguement and supporting sources edit, paper data and presentation edit, paper final edit.   

---

## 4. Conclusion

**4.1 What should the reader approve or do** after reading the proposal?
> The reader (Prof. Laurence) should be prepared to read a paper on my topic and grade it for it's effectiveness in writting a technical research paper.

**4.2 Beyond an academic exercise.** Why does this matter outside the class?
> This paper will be a foundation for the next semester of research I'll conduct while applying to graduate school. 

**4.3 Why the audience should want to read the report.** One sentence.
> The audience should read my proposal in order verify that it meets the requirements for the WRTG-316 assignment. However, the audience for the paper so that (refer to 1.4.6)

---

## 5. Works Cited

**5.1** Every source cited in the proposal goes in a Works Cited list at the end, and in-text
citations follow the same style (IEEE uses bracketed numbers, like [1]). Anything to add here,
such as a source you want cited in the introduction?
> I will complete this part using EndNote fusion. Please give me a draft or relevant information I can use to complete this. 

---

## Anything else

**6.1** Any extra heading you want (the assignment allows more than the required ones), or
anything I should know before drafting?
> Nope. 

---

## Checklist: assignment requirements → questions

| Requirement | Questions |
| --- | --- |
| Report is a formal analytical report, empirical, ~10-page body | 0.2, 0.3, 1.3.4 |
| Argument supported by evidence from other research | 1.3.2, 2.3, 2.4, 3.1 |
| Counter-arguments addressed, shown not to defeat the argument | 1.3.3, 1.4.4 |
| Unique perspective | 1.4.5 |
| Proposal about 4–5 pages | (drafting; 0.3 helps set scope) |
| Well-thought-out title | 0.1 |
| Useful graphics, if appropriate | 0.6 |
| All required headings and subheadings; extra headings as needed (e.g., audience) | Sections 1–5 follow them; 0.4, 6.1 |
| Citation style stated somewhere in the proposal | 0.5, 5.1 |
| **Introduction**, with introductory material as appropriate | 1.1 |
| *Research Issue and Its Background*: interest, historical/cultural context, treatment in scholarly and professional literature | 1.2.1–1.2.4 |
| *Research Questions and Thesis Statement*: explicit, debatable thesis | 1.3.1–1.3.3 |
| … narrow enough for 8–10 pages | 1.3.4 |
| … curiosity explained and contextualized | 1.3.5 |
| … link to the larger underlying question | 1.3.6 |
| … list of questions, known ones answered, unknown ones marked | 1.3.7 |
| *Research Subject Justification and Purpose*: so what, necessity, relevance | 1.4.1, 1.4.2 |
| … takes a position | 1.4.3 |
| … counter-arguments listed, with intent to address them | 1.4.4 |
| … originality of perspective | 1.4.5 |
| … reader's course of action and research purpose | 1.4.6, 1.4.7 |
| **Qualifications for Research on Topic X** (topic named) | 2.0 |
| *Capability*: passion, qualifying experience, capabilities needed | 2.1.1–2.1.3 |
| *Library Research Skills*: mini-course attendance acknowledged | 2.2.1 |
| … at least three subject resources, each with what it holds and why useful | 2.2.2 |
| *Review of Literature*: two most relevant sources, author and title, 1–2 paragraphs each on fit | 2.3.1, 2.3.2 |
| *Annotated Bibliography*: at least seven sources, in citation style, 1–2 sentences each, none from the Review of Literature | 2.4.1, 2.4.2 |
| **Research Plan and Methodology** / *Methods*: what and how | 3.1.1, 3.1.2 |
| … authorities; specific sites, databases, key texts, authors | 3.1.3, 3.1.4 |
| … non-text research (fieldwork, interviews, surveys, etc.) | 3.1.5 |
| … source biases and reliability | 3.1.6 |
| *Proposed Outline of Research Report* | 3.2.1 |
| *Research Timeline*: milestones and dates | 0.7, 3.3.1 |
| **Conclusion**: persuade to approve, sense of finality, return to so what, why it matters, why read it | 4.1–4.3 |
| **Works Cited**: every cited source, in-text citations in the same style | 5.1 |
