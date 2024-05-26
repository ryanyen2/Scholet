// 'bin_id', 'email', 'first_name', 'last_name', 'faculty', 'department',
//        'area_of_focus', 'gs_link', 'author_id', 'title', 'abstract', 'doi',
//        'gs_url', 'embeddings', 'umap_x', 'umap_y', 'cluster', 'kde',
//        'top_keywords', 'department_broad', 'focus_label', 'focus_tag',
//        'umap_x_bin_10', 'umap_y_bin_10', 'umap_x_bin_12', 'umap_y_bin_12',
//        'umap_x_bin_14', 'umap_y_bin_14', 'umap_x_bin_16', 'umap_y_bin_16',
//        'umap_x_bin_18', 'umap_y_bin_18', 'umap_x_bin', 'umap_y_bin',
//        'umap_x_bin_20', 'umap_y_bin_20', 'umap_x_bin_22', 'umap_y_bin_22',
//        'umap_x_bin_24', 'umap_y_bin_24', 'umap_x_bin_26', 'umap_y_bin_26',
//        'umap_x_bin_28', 'umap_y_bin_28', 'umap_x_bin_30', 'umap_y_bin_30',
//        'umap_x_bin_32', 'umap_y_bin_32', 'umap_x_bin_34', 'umap_y_bin_34',
//        'umap_x_bin_36', 'umap_y_bin_36', 'umap_x_bin_38', 'umap_y_bin_38'

export type Data = {
    bin_id: string;
    paper_id: number;
    email: string;
    first_name: string;
    last_name: string;
    faculty: FacultyType;
    department: string;
    area_of_focus: string;
    gs_link: string;
    author_id: string;
    title: string;
    abstract: string;
    doi: string;
    gs_url: string;
    embeddings: number[];
    umap_x: number;
    umap_y: number;
    cluster: number;
    kde: number;
    top_keywords: string;
    department_broad: string;
    focus_label: string;
    focus_tag: string;
    umap_x_bin_10: number; umap_y_bin_10: number; umap_x_bin_12: number; umap_y_bin_12: number; umap_x_bin_14: number; umap_y_bin_14: number; umap_x_bin_16: number; umap_y_bin_16: number; umap_x_bin_18: number; umap_y_bin_18: number; umap_x_bin: number; umap_y_bin: number; umap_x_bin_20: number; umap_y_bin_20: number; umap_x_bin_22: number; umap_y_bin_22: number; umap_x_bin_24: number; umap_y_bin_24: number; umap_x_bin_26: number; umap_y_bin_26: number; umap_x_bin_28: number; umap_y_bin_28: number; umap_x_bin_30: number; umap_y_bin_30: number; umap_x_bin_32: number; umap_y_bin_32: number; umap_x_bin_34: number; umap_y_bin_34: number; umap_x_bin_36: number; umap_y_bin_36: number; umap_x_bin_38: number; umap_y_bin_38: number;
};

export type BinData = {
    id: string;
    x: number;
    y: number;
    // summary: string;
    // keywords: string;
    width: number;
    height: number;
    // emoji: string;
    // editable?: boolean;
    selected: boolean;
    group?: string;
    data: (Data|ScholarData)[];
};

export type ScholarData = {
    id: string;
    name: string;
    x: number;
    y: number;
    faculty: FacultyType;
    department: string;
    area_of_focus: string;
    gs_link: string;
    author_id: string;
    email: string;
    data: Data[];
    selected?: boolean;
    width: number;
    height: number;
};


export type RefereneceType = {
    abstract: string;
    paper_id: string;
    score: number;
    title: string;
    name: string;
    sentences: string[];
}

export type InstructionType = "ADD_CONTEXT" | "REMOVE_CONTEXT" | "HIGHLIGHT_CONTEXT" | "OBSCURE_CONTEXT" | "GROUP_CONTEXT" | "GENERAL_CONTEXT";

export type Message = {
    id: number;
    timestamp: string;
    text: string;
    role: MessageRole;
    citations?: any[];
    user_context?: string;
    bot_context?: string;

};

export type MessageRole = "user" | "system" | "assistant" | "user-bot";

export type SelectableColumn = "cluster" | "faculty" | "department" | "focus_tag";

export type FacultyType =
    | "Engineering"
    | "Mathematics"
    | "Science"
    | "Health"
    | "Arts"
    | "Environment"
    | "Healh"
    | "";

export type CombinedData = BinData | ScholarData;