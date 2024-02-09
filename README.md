# AI Institute Visualization

## Basic Idea
The project is a visualization of the AI Institute at the University of Waterloo. The visualization will be interactive and will allow users to explore the institute's research and collaborations in a variety of ways. The visualization will be built using Svelte and D3.js.


## Project Structure
The project is structured as follows:
- `src` contains the source code for the project
  - `routes` contains the different pages of the project
  - `types` contains the typescript types
  - `static` contains the data
- `python-script` contains the python scripts for data processing, vectorization, 2d projection, and clustering


## Data
`combined_df.csv`
> This csv file contains the top cited publications from each professor from the AI Institute.

`combined_df_pubdate.csv`
> This csv file contains the latest publications from each professor from the AI Institute. The data is a combination of the author and publication data.
  
| Column Name | Description |
| ----------- | ----------- |
| email | The email of the author |
| first_name | The first name of the author |
| last_name | The last name of the author |
| faculty | The faculty author is affiliated with |
| department | The department author is affiliated with |
| area_of_focus | The self-identified area of focus of the author |
| gs_link | The link to the author's google scholar profile |
| author_id | The author's unique id |
| title | The title of the publication |
| abstract | The abstract of the publication |
| doi | The doi of the publication |
| embeddings | The embeddings of the publication |
| umap_x | The x coordinate of the 2d projection of the embeddings |
| umap_y | The y coordinate of the 2d projection of the embeddings |
| cluster | The cluster the publication belongs to (KMeans) |
| kde | The kernel density estimation of the publication |
| focus_tag | The tag of the area of focus |



## Data Preperation - Python Scripts
1. Load data (publications record from google scholar + faculty data from the AI Institute website)
2. Clean data
3. Vectorize data with all-MiniLM-L6-v2
4. 2D projection of the vectorized data (UMAP)
5. Clustering of the 2D projected data (KMeans)
6. Kernel Density Estimation of the 2D projected data
7. Extract top keywords from each cluster (TF-IDF, GPT-4)


## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://kit.svelte.dev/docs/adapters) for your target environment.


## Q&A
**Why using visual embeddings?**
> Visual embeddings are a way to represent high-dimensional data in a 2D space. This allows us to visualize the data and explore the relationships between the data points. In this project, we use UMAP to project the vectorized data into a 2D space. This allows us to visualize the relationships between the publications and the authors.

**Why using clustering?**
> Clustering is a way to group data points based on their similarity. In this project, we use KMeans to cluster the 2D projected data. This allows us to group the publications and the authors based on their similarity. This can help us identify patterns and relationships in the data.

**Why using kernel density estimation?**
> Kernel density estimation is a way to estimate the probability density function of a set of data points. In this project, we use kernel density estimation to estimate the probability density function of the 2D projected data. This allows us to visualize the distribution of the data points and identify areas of high density.

**Why using TF-IDF?**
> TF-IDF is a way to extract keywords from a set of documents. In this project, we use TF-IDF to extract keywords from the abstracts of the publications. This allows us to identify the key topics and themes in the publications.

**Why project the data into 2D space? What is UMAP**
> UMAP is a dimensionality reduction technique that is used to project high-dimensional data into a lower-dimensional space. In this project, we use UMAP to project the vectorized data into a 2D space. This allows us to visualize the relationships between the publications and the authors.

**Why use MiniLM?**
> MiniLM is a small version of the LM model that is designed for efficient vectorization of text data. In this project, we use MiniLM to vectorize the abstracts of the publications. This allows us to represent the abstracts as high-dimensional vectors, which can be projected into a 2D space and clustered.



## References
- [Svelte](https://svelte.dev/)
- [D3.js](https://d3js.org/)
- [MiniLM](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [UMAP](https://umap-learn.readthedocs.io/en/latest/)
- [KMeans](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html)
- [Kernel Density Estimation](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KernelDensity.html)
- [TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)