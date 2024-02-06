<script lang="ts">
  import type { Data } from "../types/type.ts";

  //   filteredData, selectedPaper are props from parent
  export let filteredData: Data[];
  export let selectedPaper: Data | null;


  let rowRefs = [] as HTMLTableRowElement[];


  $: if (selectedPaper) {
    const selectedIndex = filteredData.findIndex((paper) => paper.paper_id === selectedPaper!.paper_id);
    if (selectedIndex !== -1 && rowRefs[selectedIndex]) {
      rowRefs[selectedIndex].scrollIntoView({ behavior: "smooth"});
    }
  }
</script>

<div class="scrollable">
  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>Abstract</th>
        <th>Author</th>
        <th>Faculty - Department</th>
        <th>Area of Focuses</th>
        <th>Contact</th>
      </tr>
    </thead>
    <tbody>
      {#each filteredData as paper, i (paper.paper_id)}
      <!-- highlight if is the selected paper -->
        <tr bind:this={rowRefs[i]} style="background-color: {selectedPaper && selectedPaper.paper_id === paper.paper_id ? 'lightblue' : 'white'}">
          <td>{paper.title}</td>
          <td class='table_abstract'>{paper.abstract}</td>
          <!-- department, focus_tag, last_name, first_name, email, faculty, gs_link -->
          <td>{paper.first_name}, {paper.last_name}</td>
          <td>{paper.faculty} - {paper.department}</td>
          <td>{paper.focus_tag}</td>
          <td>
            <a href="mailto:{paper.email}">[Email]</a> 
            <a href="{paper.gs_link}" target="_blank">[Google Scholar]</a>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .scrollable {
    overflow: auto;
    height: 30rem;
    margin-top: 2.5rem;
    width: 100%;
  }


  table {
    width: 100%;
    height: 20vh;
    border-collapse: separate;
    border-spacing: 0;
    margin-top: 20px;
    border: 1px solid #ddd;
    border-radius: 10px;
    overflow: hidden;
    background-color: #f8f8f8;
  }
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
    transition: background-color 0.2s ease;
  }
  th {
    background-color: #afafaf;
    color: white;
  }
  tr:hover {
    background-color: #f5f5f5;
  }
  .table_abstract {
    display: -webkit-box;
    -webkit-line-clamp: 5;
    -webkit-box-orient: vertical;
    overflow: auto;
  }
  .table_abstract:hover {
    -webkit-line-clamp: none;
  }

  a {
    margin-right: 0.5em;
    color: cadetblue;
  }

  a:hover {
    text-decoration: underline;
  }
</style>
