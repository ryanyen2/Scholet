<!-- 
  === DESCRIPTION of the file ===
  This file is a svelte component that creates a scatter plot.
  It takes in a selectedColumn, vis, searchTerm, dataSource, data, and filteredData as props.
  The selectedColumn is the column that the user has selected to color the dots by.
  The vis is the div that the scatter plot will be drawn in.
  The searchTerm is the string that the user has entered to search for papers.
  The dataSource is the source of the data.
  The data is the list of papers.
  The filteredData is the list of papers that match the searchTerm.
  The chart is created using the redraw function which is called when the selectedColumn, vis, searchTerm, dataSource, or data changes.
-->

<script lang="ts">
  import { onMount } from "svelte";
  import * as d3 from "d3";
  // import type { ScaleLinear } from "d3";
  import { browser } from "$app/environment";
  import PaperInfo from "./PaperInfo.svelte";
  import HierarchicalViz from "./HierarchicalViz.svelte";

  import type { Data, SelectableColumn, FacultyType } from "../types/type.ts";

  let selectedColumn = "cluster" as SelectableColumn;
  let vis = null as any;
  let searchTerm = "" as string;
  let dataSource = "combined_df";

  let data = [] as Data[];
  let filteredData = [] as Data[];
  let selectedPaper: Data;
  let topTenPapers = [] as Data[];

  // d3.csv(`http://localhost:5173/${dataSource}.csv`).then(function (d) {
  async function loadData() {
    // let url = `http://localhost:5173/${dataSource}.csv`;
    let url = `https://raw.githubusercontent.com/ryanyen2/waterloo-ai-institute/main/static/${dataSource}.csv`;
    let d = await d3.csv(url);
    data = [];
    let index = 0;
    d.forEach(function (d) {
      data.push({
        paper_id: index++ + "",
        x: +d.umap_x * 1.1,
        y: +d.umap_y * 1.1,
        cluster: d.cluster,
        title: d.title,
        abstract: d.abstract,
        department: d.department,
        department_broad: d.department_broad,
        focus_tag: d.focus_tag,
        focus_label: d.focus_label,
        top_keywords: d.top_keywords,
        last_name: d.last_name,
        first_name: d.first_name,
        email: d.email,
        faculty: d.faculty,
        area_of_focus: d.area_of_focus,
        gs_link: d.gs_link,
        author_id: d.author_id,
        distance: 0,
      });
    });
  }

  let margin = { top: 10, right: 30, bottom: 30, left: 60 },
    width = 920 - margin.left - margin.right,
    height = 800 - margin.top - margin.bottom;

  if (browser) {
    window.addEventListener("resize", redraw);
    onMount(() => {
      loadData();
      setTimeout(redraw, 300);
      window.addEventListener("resize", redraw);
    });
  }

  function highlightSearchResults() {
    let lowerCaseSearchTerm = searchTerm.toLowerCase();

    d3.selectAll(".dot")
      .style("opacity", (d: any) => {
        let searchableString = [
          d.title,
          d.abstract,
          d.first_name,
          d.last_name,
          d.department,
        ]
          .join(" ")
          .toLowerCase();

        return searchableString.includes(lowerCaseSearchTerm) ? 1 : 0.5;
      })
      .attr("r", (d: any) => {
        let searchableString = [
          d.title,
          d.abstract,
          d.first_name,
          d.last_name,
          d.department,
        ]
          .join(" ")
          .toLowerCase();

        return lowerCaseSearchTerm.length > 1 &&
          searchableString.includes(lowerCaseSearchTerm)
          ? 10
          : 4;
      })
      // add a stroke to the selected dot
      .attr("stroke", (d: any) => {
        let searchableString = [
          d.title,
          d.abstract,
          d.first_name,
          d.last_name,
          d.department,
        ]
          .join(" ")
          .toLowerCase();

        return lowerCaseSearchTerm.length > 1 &&
          searchableString.includes(lowerCaseSearchTerm)
          ? "black"
          : "none";
      });

    if (lowerCaseSearchTerm.length > 1) {
      filteredData = data.filter((d: any) => {
        let searchableString = [
          d.title,
          d.abstract,
          d.first_name,
          d.last_name,
          d.department,
        ]
          .join(" ")
          .toLowerCase();

        return searchableString.includes(lowerCaseSearchTerm);
      });
    }
  }

  $: if (browser) dataSource, loadData(), redraw();
  $: if (browser && data.length > 0) selectedColumn, redraw();
  $: if (browser && data.length > 0) searchTerm, highlightSearchResults();

  let zoom = d3.zoom().on("zoom", handleZoom) as any;

  function handleZoom(e: any) {
    d3.select("svg g").attr("transform", e.transform);
  }

  function initZoom() {
    d3.select(vis).call(zoom);
  }

  function redraw(): void {
    d3.select(vis).html(null);

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

    const facultyColor = d3
      .scaleOrdinal()
      .domain([
        "Engineering",
        "Mathematics",
        "Science",
        "Health",
        "Arts",
        "Environment",
        "Healh",
      ])
      // art = (200, 75, 33)
      // engineering = (93, 0, 150)]
      // environment = (96, 112, 0)
      // health = (43, 93, 105)
      // mathematics = (148, 29, 107)
      // science = (19, 52, 147)
      .range([
        "#5d0096", // engineering
        "#941d6b", // mathematics
        "#133493", // science
        "#2b5d69", // health
        "#c84b21", // arts
        "#606f00", // environment
      ])
      .unknown("#f5f5f5") as any;

    const tooltip = d3
      .select("#vis")
      .append("div")
      .style("opacity", 0)
      .style("display", "none")
      .attr("class", "tooltip")
      .style("position", "absolute")
      .style("background-color", "white")
      .style("border", "solid")
      .style("border-width", "1px")
      .style("border-radius", "5px")
      .style("padding", "10px");

    function highlight(d: Data) {
      // const selected_cluster = d.cluster as string;
      const selected_column = d[selectedColumn] as string;

      if (searchTerm.length > 1) {
        return;
      }

      d3.selectAll(".dot").transition().duration(100).attr("r", 3);
      // .style("fill", "lightgrey");

      d3.selectAll(".cluster_" + selected_column)
        .transition()
        .duration(100)
        .style(
          "fill",
          selectedColumn === "faculty"
            ? facultyColor(selected_column as FacultyType)
            : color(selected_column),
        )
        .attr("r", 6);
    }

    const doNotHighlight = function (d: Data) {
      if (searchTerm.length > 1) {
        return;
      }

      d3.selectAll(".dot")
        .transition()
        .duration(100)
        .style("fill", (d: any) =>
          selectedColumn === "faculty"
            ? facultyColor(d[selectedColumn] as FacultyType)
            : color(d[selectedColumn]),
        )
        .attr("r", 4);
    };

    let xScale = d3.scaleLinear().domain([-1, 17]).range([0, width]);
    let yScale = d3
      .scaleLinear()
      .domain(dataSource === "combined_df_pubdate" ? [-1, 13] : [-4.5, 10])
      .range([height, 0]);

    // create svg and create a group inside that is moved by means of margin
    const svg = d3
      .select(vis)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${[margin.left, margin.top]})`);

    // draw x and y axes
    svg
      .append("g")
      .attr("transform", `translate(${[0, height]})`)
      .call(d3.axisBottom(xScale));
    svg.append("g").call(d3.axisLeft(yScale));

    // draw data points
    svg
      .append("g")
      .selectAll("dot")
      .data(data)
      .enter()
      .append("circle")
      .attr("class", function (d) {
        return "dot cluster_" + d[selectedColumn];
      })
      .attr("cx", function (d) {
        return xScale(d.x);
      })
      .attr("cy", function (d) {
        return yScale(d.y);
      })
      .attr("r", 4)
      .style("fill", (d) =>
        selectedColumn === "faculty"
          ? facultyColor(d[selectedColumn] as FacultyType)
          : color(d[selectedColumn]),
      )
      .style("fill-opacity", "0.75")
      .on("click", function (event, d) {
        selectedPaper = d;
        let x = selectedPaper.x;
        let y = selectedPaper.y;
        data.forEach((d) => {
          d.distance = Math.pow(d.x - x, 2) + Math.pow(d.y - y, 2);
        });
        // improve using min-heap
        data.sort((a, b) => a.distance - b.distance);
        topTenPapers = data.slice(1, 11);

        const dataLinks = topTenPapers.map((p) => ({
          source: selectedPaper,
          target: p,
        }));
        svg.selectAll("line").remove();
        svg
          .append("g")
          .selectAll("line")
          .data(dataLinks)
          .enter()
          .append("line")
          .attr("x1", function (d) {
            return xScale(d.source.x);
          })
          .attr("y1", function (d) {
            return yScale(d.source.y);
          })
          .attr("x2", function (d) {
            return xScale(d.target.x) - Math.cos(angle(d.source, d.target)) * 4;
          })
          .attr("y2", function (d) {
            return yScale(d.target.y) + Math.sin(angle(d.source, d.target)) * 4;
          })
          .style("stroke", "black")
          .style("stroke-width", 0.5);

        function angle(source: Data, target: Data) {
          return Math.atan2(target.y - source.y, target.x - source.x);
        }

        d3.selectAll(".dot")
          .transition()
          .duration(100)
          .attr("stroke", (d: any) =>
            topTenPapers.includes(d) ? "black" : "none",
          )
          .attr("stroke-width", (d: any) =>
            topTenPapers.includes(d) ? 0.5 : 0,
          );
      })
      .on("mouseover", function (event, d) {
        highlight(d);
        d3.selectAll(".dot")
          .transition()
          .duration(100)
          .attr("r", (dot: any) => filteredData.includes(dot) ? 10 : 4)
          .attr("stroke-width", (dot: any) => {
            if (filteredData.includes(dot)) {
              return 2;
            } else if (topTenPapers.includes(dot)) {
              return 0.5;
            } else {
              return 0;
            }
          })
          .attr(
            "stroke",
            (dot: any) => filteredData.includes(dot) || topTenPapers.includes(dot)
              ? "black"
              : "none",
          );

        d3.select(this)
          .transition()
          .duration(100)
          .attr("r", 12)
          .attr("stroke-width", 2)
          .attr("stroke", "black");
        tooltip.style("display", "block").style("opacity", 1);
      })
      .on("mousemove", function (event, d) {

        tooltip
          .html(
            "<b>" +
              d.title +
              "</b>" +
              "<br>" +
              "<br>" +
              "<i>" +
              d.first_name +
              " " +
              d.last_name +
              "</i>" +
              "<br>" +
              "<br>" +
              "<table>" +
              "</th></tr>" +
              "<tr><td>Area of Focus:</td><td>" +
              d.focus_tag +
              "</td></tr>" +
              "<tr><td>Department:</td><td>" +
              d.department +
              "</td></tr>" +
              "<tr><td>Faculty:</td><td>" +
              "<span style='color:" +
              facultyColor(d.faculty) +
              "'>" +
              d.faculty +
              "</span>" +
              "</td></tr>" +
              // cluster with the color
              "<tr><td>Cluster:</td><td>" +
              "<span style='color:" +
              color(d.cluster) +
              "'>" +
              d.cluster +
              "\t" +
              d.top_keywords?.split(",").slice(0, 5).join(", ") +
              "</span>" +
              "</td></tr>" +
              "</table>",
          )
          .style("display", "block")
          .style("opacity", 1)
          .style("left", event.pageX + 10 + "px")
          .style("top", event.pageY + 10 + "px");
      })
      .on("mouseleave", function (event, d) {
        console.log("leave" + JSON.stringify(d))
        doNotHighlight(d);
        d3.select(this)
          .transition()
          .duration(100)
          // if it's in the filteredData, then it should be highlighted
          .attr("r", filteredData.includes(d) ? 10 : 4)
          .attr("stroke-width", (d: any) => {
            if (filteredData.includes(d)) {
              return 2;
            } else if (topTenPapers.includes(d)) {
              return 0.5;
            } else {
              return 0;
            }
          })
          .attr(
            "stroke",
            filteredData.includes(d) || topTenPapers.includes(d)
              ? "black"
              : "none",
          );

        tooltip.style("display", "none").style("opacity", 0);
      });

    svg.selectAll(".legend").remove();

    let column_values = {} as Set<string> | Map<string, string>;
    if (selectedColumn === "cluster") {
      // only show the top 5 keywords, remove all double quotes

      column_values = new Map(
        data.map((d) => [
          d.cluster,
          d.top_keywords.split(",").slice(0, 5).join(", ").replace(/"/g, ""),
        ]),
      );
      // column_values = new Map(data.map((d) => [d.cluster, d.top_keywords]));
    } else {
      column_values = new Set(data.map((d) => d[selectedColumn]));
    }

    if (column_values instanceof Set) {
      column_values = new Set(Array.from(column_values).sort());
    } else {
      column_values = new Map(
        Array.from(column_values).sort((a, b) => {
          return parseInt(a[0]) - parseInt(b[0]);
        }),
      );
    }

    // Create the legend
    let legend = svg
      .selectAll(".legend")
      .data(
        selectedColumn === "faculty"
          ? Array.from(column_values as Set<string>)
          : Array.from(column_values as Map<string, string>, ([key, _]) => key),
      )
      .enter()
      .append("g")
      .attr("class", "legend")
      .attr("transform", (d, i) => "translate(0," + i * 20 + ")");

    // colored rectangles
    legend
      .append("rect")
      .attr("x", 20)
      .attr("width", 18)
      .attr("height", 18)
      .style("fill", selectedColumn === "faculty" ? facultyColor : color);

    // Add the text labels
    legend
      .append("text")
      .attr("x", 50)
      .attr("y", 9)
      .attr("dy", ".35em")
      .style("text-anchor", "start")
      .text((d: any) => {
        return selectedColumn === "faculty"
          ? d
          : (column_values as Map<string, string>).get(d);
      });

    initZoom();
  }
</script>

<main>
  <div class="container">
    <div>
      <select bind:value={dataSource}>
        <option value="combined_df">Combined Data</option>
        <option value="combined_df_pubdate">Most Recent Data</option>
      </select>
      <select bind:value={selectedColumn}>
        <option value="cluster">Cluster</option>
        <option value="faculty">Faculty</option>
        <!-- disable the following two -->
        <option value="department" disabled>Department</option>
        <option value="focus_tag" disabled>Focus Tag</option>
      </select>
      <input
        type="text"
        bind:value={searchTerm}
        placeholder="Search Name, Paper, Department..."
      />
      <div id="vis" bind:this={vis}></div>
    </div>
    <div class="side_panel">
      <div>
        <PaperInfo {filteredData} {selectedPaper} />
      </div>
      <div>
        <HierarchicalViz {selectedPaper} {data} />
      </div>
    </div>
  </div>
</main>

<style>
  main {
    height: 100%;
  }

  .container {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    height: 100%;
  }

  .side_panel {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
  }

  #vis {
    width: 100%;
    /* height: 100%; */
    background-color: #f5f5f5;
  }

  /* search input */
  input {
    width: 40%;
    padding: 12px 20px;
    margin: 8px 0;
    box-sizing: border-box;
    border: 1px solid #ccc;
    border-radius: 8px;
  }

  /* select */
  select {
    width: 15%;
    padding: 12px 20px;
    margin: 8px 0;
    box-sizing: border-box;
    border: 1px solid #ccc;
    border-radius: 8px;
  }
</style>
