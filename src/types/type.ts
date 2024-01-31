export type Data = {
    x: number;
    y: number;
    paper_id: string;
    cluster: string;
    title: string;
    abstract: string;
    department: string;
    department_broad: string;
    focus_tag: string;
    focus_label: string;
    top_keywords: string;
    last_name: string;
    first_name: string;
    email: string;
    faculty: string;
    area_of_focus: string;
    gs_link: string;
    author_id: string;
};

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