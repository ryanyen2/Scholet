import os 
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from umap import UMAP
from sklearn.cluster import KMeans
from sklearn.neighbors import KernelDensity
from heapq import nlargest
from sklearn.feature_extraction.text import TfidfVectorizer
tfidf = TfidfVectorizer(stop_words='english')

model = SentenceTransformer('all-MiniLM-L6-v2')
_BATCH_SIZE = 128
_BINS_NUM = 20
_CLUSTER_NUM = 5
_TOP_KERWORDS = 5


class DataStore:
    def __init__(self):
        # self.embeddings_dfs = {}
        self.embeddings_df = pd.DataFrame(columns=['email', 'first_name', 'last_name', 'faculty', 'department',
       'area_of_focus', 'gs_link', 'author_id', 'title', 'abstract', 'doi',
       'gs_url', 'embeddings', 'umap_x', 'umap_y', 'cluster', 'kde',
       'top_keywords', 'department_broad', 'focus_label', 'focus_tag',
       'umap_x_bin_10', 'umap_y_bin_10', 'umap_x_bin_12', 'umap_y_bin_12',
       'umap_x_bin_14', 'umap_y_bin_14', 'umap_x_bin_16', 'umap_y_bin_16',
       'umap_x_bin_18', 'umap_y_bin_18', 'umap_x_bin', 'umap_y_bin',
       'umap_x_bin_20', 'umap_y_bin_20', 'umap_x_bin_22', 'umap_y_bin_22',
       'umap_x_bin_24', 'umap_y_bin_24', 'umap_x_bin_26', 'umap_y_bin_26',
       'umap_x_bin_28', 'umap_y_bin_28', 'umap_x_bin_30', 'umap_y_bin_30',
       'umap_x_bin_32', 'umap_y_bin_32', 'umap_x_bin_34', 'umap_y_bin_34',
       'umap_x_bin_36', 'umap_y_bin_36', 'umap_x_bin_38', 'umap_y_bin_38'])

    def load_data(self):
        csv_path = os.path.join('./data', 'ieee_vis_embed.csv')
        df = pd.read_csv(csv_path)
        df['paper_id'] = df.index
        df['embeddings'] = df['embeddings'].apply(eval)
        df['bin_id'] = df.apply(lambda x: f'{x["umap_x_bin_30"]}_{x["umap_y_bin_30"]}', axis=1)
        self.embeddings_df = df

    def get_data(self):
        return self.embeddings_df
    

    def update_data(self, row):
        content = row['content']
        embeddings = model.encode(content, batch_size=_BATCH_SIZE)
        row['embeddings'] = embeddings
        self.embeddings_df.loc[len(self.embeddings_df)] = row
        self.embeddings_df = umap(self.embeddings_df)
        self.embeddings_df = kmeans(self.embeddings_df)
        self.embeddings_df = kde(self.embeddings_df)
        self.embeddings_df = cluster_keywords_extraction(self.embeddings_df)
        self.embeddings_df = data_binning(self.embeddings_df)
        
        return self.embeddings_df
        
    def update_params(self, bins_num, cluster_num):
        global _BINS_NUM
        global _CLUSTER_NUM
        _BINS_NUM = bins_num
        _CLUSTER_NUM = cluster_num
        
        self.embeddings_df = kmeans(self.embeddings_df, cluster_num)
        self.embeddings_df = cluster_keywords_extraction(self.embeddings_df)
        self.embeddings_df = data_binning(self.embeddings_df, bins_num)
        
        return self.embeddings_df


data_store = DataStore()
data_store.load_data()


def umap(embeddings_df):
    # UMAP
    embeddings = np.array(embeddings_df['embeddings'].tolist())
    
    umap = UMAP(n_components=2, n_neighbors=40, min_dist=0.01)
    umap_embeddings = umap.fit_transform(embeddings)
    embeddings_df['umap_x'] = umap_embeddings[:, 0]
    embeddings_df['umap_y'] = umap_embeddings[:, 1]
    
    return embeddings_df


def kmeans(embeddings_df, n_clusters=_CLUSTER_NUM):
    # KMeans
    embeddings = np.array(embeddings_df['embeddings'].tolist())
    
    kmeans = KMeans(n_clusters=n_clusters)
    embeddings_df['cluster'] = kmeans.fit_predict(embeddings)
    
    return embeddings_df


def kde(embeddings_df):
    # KDE
    embeddings = np.array(embeddings_df['embeddings'].tolist())
    
    kde = KernelDensity(bandwidth=0.5)
    kde.fit(embeddings)
    embeddings_df['density'] = kde.score_samples(embeddings)
    
    return embeddings_df


def cluster_keywords_extraction(embeddings_df, top_n=_TOP_KERWORDS):
    # Keyword extraction
    cluster_keywords = {}
    for cluster in embeddings_df['cluster'].unique():
        cluster_df = embeddings_df[embeddings_df['cluster'] == cluster]
        cluster_content = cluster_df['content']
        
        cluster_tfidf = tfidf.fit_transform(cluster_content)
        feature_names = tfidf.get_feature_names_out()
        dense = cluster_tfidf.todense()
        episode_keywords = dense[0].tolist()[0]
        phrase_scores = [pair for pair in zip(range(0, len(episode_keywords)), episode_keywords) if pair[1] > 0]
        sorted_phrase_scores = sorted(phrase_scores, key=lambda t: t[1] * -1)
        keywords = []
        for phrase, score in [(feature_names[word_id], score) for (word_id, score) in sorted_phrase_scores][:top_n]:
            keywords.append(phrase)
        cluster_keywords[cluster] = keywords
        
    embeddings_df['cluster_keywords'] = embeddings_df['cluster'].map(cluster_keywords)
    return embeddings_df


def document_keywords_extraction(embeddings_df, top_n=_TOP_KERWORDS):
    # Keyword extraction
    document_keywords = {}
    for doc_id in embeddings_df['doc_id'].unique():
        doc_df = embeddings_df[embeddings_df['doc_id'] == doc_id]
        doc_content = doc_df['content']
        
        doc_tfidf = tfidf.fit_transform(doc_content)
        feature_names = tfidf.get_feature_names_out()
        dense = doc_tfidf.todense()
        episode_keywords = dense[0].tolist()[0]
        phrase_scores = [pair for pair in zip(range(0, len(episode_keywords)), episode_keywords) if pair[1] > 0]
        sorted_phrase_scores = sorted(phrase_scores, key=lambda t: t[1] * -1)
        keywords = []
        for phrase, score in [(feature_names[word_id], score) for (word_id, score) in sorted_phrase_scores][:top_n]:
            keywords.append(phrase)
        document_keywords[doc_id] = keywords
        
    embeddings_df['document_keywords'] = embeddings_df['doc_id'].map(document_keywords)
    return embeddings_df


def data_binning(embeddings_df, bins_num=_BINS_NUM):
    # Binning
    embeddings_df['umap_x_bin'] = pd.cut(embeddings_df['umap_x'], bins=bins_num, labels=False)
    embeddings_df['umap_y_bin'] = pd.cut(embeddings_df['umap_y'], bins=bins_num, labels=False)
    
    unique_bins_combinations = embeddings_df[['umap_x_bin', 'umap_y_bin']].drop_duplicates()
    
    # generate bins summaries & keywords
    bin_summaries = {}
    bin_keywords = {}
    for _, row in unique_bins_combinations.iterrows():
        bin_df = embeddings_df[(embeddings_df['umap_x_bin'] == row['umap_x_bin']) & (embeddings_df['umap_y_bin'] == row['umap_y_bin'])]
        bin_content = bin_df['content'].values.tolist()
        
        tfidf_matrix = tfidf.fit_transform(bin_content)
        feature_names = tfidf.get_feature_names_out()
        dense = tfidf_matrix.todense()
        episode_keywords = dense[0].tolist()[0]
        phrase_scores = [pair for pair in zip(range(0, len(episode_keywords)), episode_keywords) if pair[1] > 0]
        sorted_phrase_scores = sorted(phrase_scores, key=lambda t: t[1] * -1)
        keywords = []
        for phrase, score in [(feature_names[word_id], score) for (word_id, score) in sorted_phrase_scores][:10]:
            keywords.append(phrase)
            
        bin_keywords[(row['umap_x_bin'], row['umap_y_bin'])] = keywords
        
        select_length = int(len(bin_content) * 0.1)
        if select_length == 0:
            select_length = 1
            
        bin_summary = nlargest(select_length, bin_content, key=len)
        bin_summary_str = ' '.join(bin_summary)
        bin_summaries[(row['umap_x_bin'], row['umap_y_bin'])] = bin_summary_str
        
    
    embeddings_df['bin_id'] = embeddings_df.apply(lambda x: f'{x["umap_x_bin"]}_{x["umap_y_bin"]}', axis=1)
    embeddings_df['bin_summary'] = embeddings_df.apply(lambda row: bin_summaries[(row['umap_x_bin'], row['umap_y_bin'])], axis=1)
    embeddings_df['bin_keywords'] = embeddings_df.apply(lambda row: bin_keywords[(row['umap_x_bin'], row['umap_y_bin'])], axis=1)
    
    return embeddings_df