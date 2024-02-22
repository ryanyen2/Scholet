<!-- 
  === DESCRIPTION of the file ===
  This file is a svelte component that creates a radial bar chart. 
  It takes in a selectedPaper and data as props. 
  The selectedPaper is the paper that the user has clicked on and the data is the list of papers. 
  The chart shows the number of papers written by each author in the same cluster as the selectedPaper. 
  The chart is created using the redraw function which is called when the selectedPaper or data changes. 
-->
<script lang="ts">
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import * as d3 from "d3";
  import type { Data } from "../types/type.ts";

  export let selectedPaper: Data;
  export let data: Data[];

  // Color scale based on 'cluster' column, 10 colors
  const color = d3
    .scaleOrdinal()
    .domain(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
    .range([
      "#1f77b4", // muted blue
      "#ff7f0e", // safety orange
      "#2ca02c", // cooked asparagus green
      "#d62728", // brick red
      "#9467bd", // muted purple
      "#8c564b", // chestnut brown
      "#e377c2", // raspberry yogurt pink
      "#7f7f7f", // middle gray
      "#bcbd22", // curry yellow-green
      "#17becf", // blue-teal
    ]) as any;

  let barVis: HTMLDivElement;
  let margin = { top: 10, right: 10, bottom: 100, left: 50 },
    width = 600 - margin.left - margin.right,
    height = 400 - margin.top - margin.bottom;

  let selectedCluster = selectedPaper?.cluster || "0";

  async function redraw() {
    d3.select(barVis).select("svg").remove();

    // let data = (await d3.csv(`https://raw.githubusercontent.com/ryanyen2/waterloo-ai-institute/main/static/${dataSource}.csv`)) as any;

    // cluster: string, count: [[professor: string, count: number]]
    const paperCounts = Array.from(
      d3.rollups(
        data,
        (v: Data[]) => v.length,
        (d: Data) => d.cluster, // group by cluster
        (d: Data) => d.first_name + " " + d.last_name
      ),
      ([key, value]) =>
        ({ cluster: key[0], count: value }) as {
          cluster: string;
          count: Array<[string, number]>;
        }
    ) as { cluster: string; count: Array<[string, number]> }[];

    const selectedClusterData = paperCounts.find(
      (d) => d.cluster === selectedCluster
    ) as { cluster: string; count: Array<[string, number]> };

    if (!selectedClusterData) {
      return;
    }

    selectedClusterData.count = selectedClusterData?.count.filter(
      (d) => d[1] > 2
    );

    selectedClusterData.count = selectedClusterData?.count.sort(
      (a, b) => b[1] - a[1]
    );

    // Scales
    const x = d3
      .scaleBand()
      .range([0, width])
      .domain(selectedClusterData.count.map((d) => d[0]));

    const y = d3
      .scaleRadial()
      .range([height, 0])
      .domain([0, d3.max(selectedClusterData.count, (d: any) => d[1])]);

    const svg = d3
      .select(barVis)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    svg
      .append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end");
    svg.append("g").call(d3.axisLeft(y));

    // Bars plot
    svg
      .selectAll("rect")
      .data(selectedClusterData.count)
      .enter()
      .append("rect")
      .attr("x", (d: any): any => x(d[0]))
      .attr("width", x.bandwidth())
      .attr("height", (d) => height - y(0))
      .attr("y", (d) => {
        return y(0);
      })
      .attr("opacity", 0.7)
      .attr("fill", color(selectedCluster))
      // add border if is selectedPaper's author
      .attr("stroke", (d) =>
        selectedPaper?.first_name + " " + selectedPaper?.last_name === d[0]
          ? "black"
          : "none"
      )
      .attr("stroke-width", (d) =>
        selectedPaper?.first_name + " " + selectedPaper?.last_name === d[0]
          ? 2
          : 0
      )
      .on("mouseover", function (d, i) {
        d3.select(this).attr("opacity", 1);
      })
      .on("mouseout", function (d, i) {
        d3.select(this).attr("opacity", .7);
      });

    svg
      .selectAll("rect")
      .transition()
      .duration(400)
      .attr("y", function (d: any) {
        return y(d[1]);
      })
      .attr("height", function (d: any) {
        return height - y(d[1]);
      })
      .delay(function (d, i) {
        return i * 50;
      });
  }

  if (browser) {
    onMount(async () => {
      redraw();
    });
  }

  $: if (browser && selectedPaper) {
    selectedCluster = selectedPaper.cluster;
    redraw();
  }

  $: if (browser && data) {
    redraw();
  }
</script>

<div>
  <div id="bar-vis" bind:this={barVis}></div>
</div>

<style>
  #bar-vis {
    width: 100%;
    height: 100%;
  }

  svg {
    width: 100%;
    height: 100%;
  }
  circle {
    fill: #69b3a2;
  }
  path {
    fill: none;
    stroke: #ccc;
  }
</style>
