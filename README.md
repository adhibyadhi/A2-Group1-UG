# A2-Group1-UG
Working repository for Social Media & Network Analysis – Assignment 2

**Group: Undergraduate (UG) Group 1**
- Joshua Steinke [s4091863]
- Paul Venatt [s4089896]
- Putu Adhi Wiguna [s4097286]

## The Project Aim
This project aims to analyse how YouTube audiences discuss the impact of artificial intelligence on the music sector. The analysis uses YouTube comments collected from videos related to the query "AI on music".

The project combines text analysis and social network analysis to investigate both the content of the discussion and the interaction patterns between users. Specifically, the project aims to:

1. Identify the main themes discussed in YouTube comments about AI and music using LDA topic modelling;
2. Analyse user sentiment toward AI’s role in the music sector using VADER sentiment analysis;
3. Construct a directed weighted user reply network from YouTube comment replies;
4. Identify influential users using SNA centrality measures;
5. Detect user communities in the reply network;
6. Compare topics and sentiment across communities to understand how different user groups frame AI’s impact on music.

Overall, the project explores whether YouTube discussion about AI and music is mainly focused on creative opportunities, industry disruption, copyright concerns, human creativity, or broader social adaptation to AI.

### How to Run the Notebook
The main analysis notebook is: `s4091863_UG_Group_1.ipynb`. Things to note before running the notebook:
1. Ensure that you have all packages listed in cell [1] with the comment "# Libraries used"
2. Change the `dataset` file path inside the cell under "**1. Exploratory Data Analysis (EDA)**" into the path where you store the data representative file.
3. You can run the notebook by executing the cells from top to bottom, or just simply, by pressing **Run All**
4. Wait until all cells finished executing