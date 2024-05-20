<script lang="ts">
  import * as d3 from "d3";
  import { createEventDispatcher } from "svelte";
  import type { RefereneceType, BinData, ScholarData } from "../types/type.js";
  import Citation from "./Citation.svelte";

  const dispatch = createEventDispatcher();
  export let scholarView: boolean = false;
  export let selectedBins: BinData[] = [];
  export let selectedScholars: ScholarData[] = [];
  export let scholarData: ScholarData[] = [];
  export let binData: BinData[] = [];

  let answerParts = [] as Array<{
    type: "text" | "citation";
    content?: string;
    id?: string;
    gradient?: string;
  }>;

  const clusterColor = d3
    .scaleOrdinal()
    .domain(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
    .range([
      "#4e79a7",
      "#f28e2b",
      "#e15759",
      "#76b7b2",
      "#59a14f",
      "#edc949",
      "#b07aa1",
      "#ff9da7",
      "#9c755f",
      "#bab0ac",
    ]) as any;

  let query = "";
  let answer = "";
  let references = [] as RefereneceType[];

  const sendQuery = async () => {
    answer = "Retrieving Relevant Information...";
    answerParts = [];

    let queryWithSelected = query;
    if (selectedScholars.length > 0) {
      queryWithSelected +=
        " " +
        selectedScholars
          .map((scholar) => `[[Researcher: ${scholar.name}]]`)
          .join(" ");
    }

    if (selectedBins.length > 0) {
      // get all paper_ids from selectedBins
      let paperIds = [] as string[];
      for (const bin of selectedBins) {
        if ("paper_id" in bin.data[0]) {
          for (const d of bin.data as any) {
            paperIds.push(d.paper_id);
          }
        } else {
          for (const d of bin.data as any) {
            for (const p of d.data as any) {
              paperIds.push(p.paper_id);
            }
          }
        }
      }
      queryWithSelected += " " + paperIds.map((id) => `[[P:${id}]]`).join(" ");
    }

    console.log(queryWithSelected);

    await fetch("http://localhost:8000/retrieval", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: queryWithSelected }),
    })
      .then((res) => res.json())
      .then((data) => {
        data = JSON.parse(data);
        console.log(data);
        references = [...data];
      });

    dispatch("retrievedReferences", references);

    // context = [{id: "paper_id", text: "abstract"}]
    const context = references.map((ref) => {
      return {
        id: ref.paper_id,
        author: ref.name,
        title: ref.title,
        text: ref.abstract,
      };
    });

    answer = "Synthesizing Information...";
    const res = await fetch("http://localhost:8000/rag", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt: query, context }),
    });

    let result = "";
    // @ts-ignore
    const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      result += value;
      answer = result;
    }

    processResult(result);
  };

  function processResult(result: string) {
    answerParts = [];

    let lastIndex = 0;
    let match;
    const regex = /\[citation:(.*?)\]/g;
    while ((match = regex.exec(result)) !== null) {
      if (match.index > lastIndex) {
        answerParts.push({
          type: "text",
          content: result.slice(lastIndex, match.index),
        });
      }

      const id = match[1];

      let bin: BinData | undefined;
      if ("cluster" in binData[0].data[0]) {
        bin = binData.find((d: any) => {
          return d.data.some((data: any) => data.paper_id.toString() === id);
        });
      } else {
        bin = binData.find((d: any) => {
          return d.data.some((scholar: ScholarData) =>
            scholar.data.some((p: any) => p.paper_id.toString() === id),
          );
        });
      }
      if (bin) {
        const clusterCounts: { [cluster: string]: number } = {};
        bin.data.forEach((p: any) => {
          const cluster = p.cluster.toString();
          if (cluster in clusterCounts) {
            clusterCounts[cluster]++;
          } else {
            clusterCounts[cluster] = 1;
          }
        });
        const sortedClusters = Object.entries(clusterCounts).sort(
          (a, b) => b[1] - a[1],
        );

        let offset = 0;
        const colorStops = sortedClusters
          .map(([cluster, count]) => {
            const colorStop = `${clusterColor(cluster)} ${offset}%`;
            offset += (count / bin.data.length) * 100;
            return colorStop;
          })
          .join(", ");

        let gradient = `linear-gradient(90deg, ${colorStops})`;

        answerParts.push({
          type: "citation",
          id,
          gradient,
        });
      } else {
        answerParts.push({
          type: "citation",
          id,
        });
      }

      lastIndex = regex.lastIndex;
    }

    // Add the text after the last citation
    if (lastIndex < result.length) {
      answerParts.push({
        type: "text",
        content: result.slice(lastIndex),
      });
    }
  }

  function handleCitationClick(e: CustomEvent<string>) {
    dispatch("citationClick", e.detail);
  }
</script>

<div id="chat-panel">
  <input
    type="text"
    bind:value={query}
    on:keydown={(e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        if (query.trim() !== "") {
          sendQuery();
        }
      }
    }}
    placeholder="Enter your question here"
  />

  <div id="qa-section">
    <!-- <p>{@html answer}</p> -->
    {#if answerParts.length > 0}
      <p>
        {#each answerParts as part (part.id ? part.id + Math.random() : Math.random())}
          {#if part.type === "text"}
            <span>{@html part.content}</span>
          {:else if part.type === "citation"}
            <Citation
              id={part.id}
              gradient={part.gradient}
              on:click={handleCitationClick}
            />
          {/if}
        {/each}
      </p>
    {:else if answer}
      <p>{answer}</p>
    {/if}
  </div>

  <div id="references">
    <table>
      <thead>
        {#if references.length > 0}
          <tr>
            <th>Author</th>
            <th>Title</th>
            <th>Abstract</th>
          </tr>
        {/if}
      </thead>
      <tbody>
        {#each references as ref (ref.paper_id + Math.random())}
          <tr>
            <td>{ref.name}</td>
            <td>{ref.title}</td>
            <td
              >{ref.abstract.substring(0, 100) +
                "..." +
                ref.abstract.substring(ref.abstract.length - 100)}</td
            >
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>

<style>
  #chat-panel {
    display: flex;
    flex-direction: column;
    /* justify-content: flex-start;
    align-items: stretch; */
    max-height: 95vh;
  }

  #chat-panel input {
    border-radius: 5px;
    border: 1px solid #3498db;
    padding: 10px;
    margin-bottom: 10px;
  }

  #qa-section {
    margin-top: 1em;
    flex: 0.4;
    min-height: 30vh;
    overflow-y: auto;
    padding: 0.2em;
  }

  #references {
    flex-grow: 1;
    overflow-y: scroll;
    width: 100%;
    min-height: 30vh;
  }

  #references table {
    width: 100%;
    border-collapse: collapse;
  }

  #references th,
  #references td {
    padding: 8px;
    border-bottom: 1px solid #bdc3c7;
  }

  #references th {
    /* background-color: #3498db; */
    /* color: white; */
    border-top: 1px solid #34495e;
    border-bottom: 1px solid #34495e;
  }

  #references tr:last-child td {
    border-bottom: 1px solid #34495e;
  }

  /* #references tr:nth-child(even) {
    background-color: #f2f2f2;
  } */

  #references tr:hover {
    background-color: #eeeeee;
  }
</style>
