<script lang="ts">
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import * as d3 from "d3";
  import type {
    Data,
    BinData,
    ScholarData,
    RefereneceType,
  } from "../types/type.js";
  // import { createEventDispatcher } from "svelte";
  // import { Marked } from "@ts-stack/markdown";
  import Chat from "./Chat.svelte";

  let userId = "" as string;
  let scholarView = false as boolean;

  let data: Data[];
  let binData: BinData[];
  let scholarData: ScholarData[];

  let svg = null as any;
  let tooltip = null as any;
  let tooltipTimeout = null as any;
  let binSize = 10;
  let g = null as any;
  let binPlot = null as any;

  let filteredBins = [] as BinData[];
  let selectedBins = [] as BinData[];
  let backgroundDots = [] as any[];

  let filteredScholars = [] as ScholarData[];

  // control input
  let binsNum = 20;
  let clusterNum = 5;
  let searchTerm = "" as string;

  let isSelectAll = false as boolean;

  let margin = { top: 30, right: 60, bottom: 40, left: 60 },
    width = 820 - margin.left - margin.right,
    height = 720 - margin.top - margin.bottom;

  let xScale = d3.scaleLinear().domain([0, width]).range([0, width]);
  let yScale = d3.scaleLinear().domain([0, height]).range([height, 0]);

  let timeout = null as any;

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

  let longTermVis: HTMLDivElement;

  function constructBinData(data: Data[]): BinData[] {
    const binsMap = new Map<string, BinData>();

    for (const point of data) {
      // df['bin_id'] = df.apply(lambda x: f'{x["umap_x_bin"]}_{x["umap_y_bin"]}', axis=1)
      const binId = `${point[`umap_x_bin_${binsNum}` as keyof Data]}_${point[`umap_y_bin_${binsNum}` as keyof Data]}`;
      let binData = binsMap.get(binId);

      if (!binData) {
        binData = {
          id: binId,
          x: point[`umap_x_bin_${binsNum}` as keyof Data] as number,
          y: point[`umap_y_bin_${binsNum}` as keyof Data] as number,
          width: binSize,
          height: binSize,
          selected: false,
          data: [],
        };
        binsMap.set(binId, binData);
      }
      binData.data.push(point);
    }

    return Array.from(binsMap.values());
  }

  function constructBackgroundDots() {
    const x = d3.scaleLinear().domain([0, width]).range([0, width]);
    const y = d3.scaleLinear().domain([0, height]).range([height, 0]);

    for (let i = -width * 0.3; i < width * 1.3; i += 20) {
      for (let j = -height * 0.3; j < height * 1.3; j += 20) {
        backgroundDots.push({ x: x(i), y: y(j) });
      }
    }

    g.selectAll(".background-dot")
      .data(backgroundDots)
      .join("circle")
      .attr("class", "background-dot")
      .attr("cx", (d: any) => d.x)
      .attr("cy", (d: any) => d.y)
      .attr("r", 1)
      .attr("fill", "#bdc3c7")
      .style("fill-opacity", 0.08);
  }

  async function redraw() {
    d3.select(longTermVis).select("svg").remove();
    d3.select(longTermVis).selectAll(".tooltip").remove();

    const minDataX = d3.min(binData, (d) => d.x) as number;
    const maxDataX = d3.max(binData, (d) => d.x) as number;
    const minDataY = d3.min(binData, (d) => d.y) as number;
    const maxDataY = d3.max(binData, (d) => d.y) as number;
    // width = longTermVis.clientWidth * 0.75 - margin.left - margin.right;

    xScale = d3.scaleLinear().domain([minDataX, maxDataX]).range([0, width]);
    yScale = d3.scaleLinear().domain([minDataY, maxDataY]).range([height, 0]);
    width = maxDataX;
    height = maxDataY;

    svg = d3
      .select(longTermVis)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom);
    g = svg
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    constructBackgroundDots();

    tooltip = d3
      .select(longTermVis)
      .append("div")
      .style("opacity", 0)
      .attr("class", "tooltip")
      .style("position", "absolute")
      .style("background-color", "white")
      .style("border", "solid")
      .style("border-width", "1px")
      .style("border-radius", "5px")
      .style("padding", "10px");

    svg
      .append("clipPath")
      .attr("id", "clip")
      .append("rect")
      .attr("width", width)
      .attr("height", height);

    let zoom = d3.zoom().on("zoom", handleZoom);

    function handleZoom(e: any) {
      g.attr("transform", e.transform);
    }

    svg.call(zoom);
    drawBins();

    svg.selectAll(".legend").remove();
    const legend = svg
      .append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${20}, ${20})`);

    let allKeywords = binData.flatMap((bin) => {
      return bin.data.map((d: Data) => {
        return { cluster: d.cluster, keywords: d.top_keywords };
      });
    }) as { cluster: number; keywords: string }[];

    // remove duplicates
    allKeywords = allKeywords.filter(
      (v, i, a) => a.findIndex((t) => t.cluster === v.cluster) === i
    ) as { cluster: number; keywords: string }[];

    legend
      .selectAll(".legend-item")
      .data(allKeywords)
      .join("g")
      .attr("class", "legend-item")
      .attr("transform", (d: any, i: number) => `translate(0, ${i * 20})`)
      .each(function (d: any) {
        // @ts-ignore
        const that = this;
        // console.log(d.cluster, clusterColor(d.cluster));
        d3.select(that)
          .append("rect")
          .attr("x", 0)
          .attr("y", 0)
          .attr("width", 10)
          .attr("height", 10)
          .attr("fill", clusterColor(d.cluster.toString()));

        d3.select(that)
          .append("text")
          .attr("x", 12)
          .attr("y", 8)
          .text(
            d.keywords
              .split(", ")
              .slice(0, 4)
              .join(", ")
              .replace(/['"[\]]/g, "")
          )
          .attr("fill", "#2C3E50")
          .style("font-size", "12px")
          .style('fill-opacity', 0.6)
          .on("mouseover", function () {
            d3.select(this).style("fill-opacity", 1);
          })
          .on("mouseleave", function () {
            d3.select(this).style("fill-opacity", 0.6);
          });
      })
  }

  function drawBins() {
    binPlot = g
      .append("g")
      .attr("clip-path", "url(#clip)")
      .selectAll(".bin-group")
      .data(binData)
      .join("g")
      .attr("class", "bin-group");

    binPlot
      .append("rect")
      .attr("class", "rectBin")
      .attr("x", (d: BinData) => d.x)
      .attr("y", (d: BinData) => d.y)
      .attr("width", (d: BinData) => d.width)
      .attr("height", (d: BinData) => d.height)
      .attr("fill", function (d: BinData) {
        const totalPoints = d.data.length;
        let groupedByCluster = d3.group(d.data, (p) => p.cluster);

        // sort by cluster size
        groupedByCluster = new Map(
          Array.from(groupedByCluster).sort((a, b) => {
            return b[1].length - a[1].length;
          })
        );

        // @ts-ignore
        const defs = d3.select(this.parentNode).append("defs");
        let gradientId = `gradient-${Math.random().toString(36).slice(2, 9)}`;
        let gradient = defs
          .append("linearGradient")
          .attr("id", gradientId)
          .attr("x1", "0%")
          .attr("y1", "0%")
          .attr("x2", "100%")
          .attr("y2", "100%");

        if (totalPoints === 1) {
          return clusterColor(d.data[0].cluster.toString());
        }

        let accumulated = 0;
        groupedByCluster.forEach((value, key) => {
          const clusterSize = value.length;
          const portion = accumulated / totalPoints;
          const nextPortion = (accumulated + clusterSize) / totalPoints;
          gradient
            .append("stop")
            .attr("offset", `${portion * 100}%`)
            .attr("stop-color", clusterColor(key.toString()));
          gradient
            .append("stop")
            .attr("offset", `${nextPortion * 100}%`)
            .attr("stop-color", clusterColor(key.toString()));
          accumulated += clusterSize;
        });

        return `url(#${gradientId})`;
      })
      .attr("rx", Math.min(binSize / 5, 15))
      .attr("ry", Math.min(binSize / 5, 15))
      .on("mouseover", async function (event: any, d: any) {
        // Group data by unique first_name + last_name
        const groupedData = d.data.reduce((acc: any, p: any) => {
          const name = `${p.first_name} ${p.last_name}`;
          if (!acc[name]) {
            acc[name] = { titles: [], cluster: p.cluster };
          }
          acc[name].titles.push(p.title);
          return acc;
        }, {});

        let tableHtml = "<table>";
        for (const name in groupedData) {
          const color = clusterColor(groupedData[name].cluster.toString());
          tableHtml += `<tr><td style="color: ${color}"><b>${name}</b></td><td><table>`;
          for (const title of groupedData[name].titles) {
            tableHtml += `<tr><td>${title}</td></tr>`;
          }
          tableHtml += "</table></td></tr><tr><td colspan='2'><hr></td></tr>"; // Add horizontal line
        }
        tableHtml += "</table>";

        tooltipTimeout = setTimeout(() => {
          tooltip.transition().style("display", "block").style("opacity", 0.9);
          tooltip
            .html(`${tableHtml}`)
            .style("left", event.pageX - 20 + "px")
            .style("top", event.pageY - 28 + "px")
            .style(
              "border",
              `1px solid ${clusterColor(d.data[0].cluster.toString())}`
            )
            .style("height", "300px")
            .style("overflow", "auto");
        }, 500);
      })
      .on("mouseleave", function (event: any, d: any) {
        clearTimeout(tooltipTimeout);
        tooltip.style("display", "none").style("opacity", 0);
      })
      .style("fill-opacity", (d: BinData) => {
        return d.data.length * 0.5;
      })
      .style("stroke", (d: BinData) => (d.selected ? "#2C3E50" : "none"))
      .style("stroke-width", 2)
      .on("click", (event: any, d: BinData) => {
        tooltip.style("display", "none").style("opacity", 0);
        d.selected = !d.selected;
        if (d.selected) {
          selectedBins.push(d);
        } else {
          selectedBins = selectedBins.filter((bin) => bin.id !== d.id);
        }

        selectedBins = Array.from(new Set(selectedBins));

        d3.selectAll(".rectBin").style("stroke", (d: any) =>
          d.selected ? "#2C3E50" : "none"
        );
      })
      .style("opacity", 0)
      .transition()
      .duration(500)
      .delay(() => Math.random() * 200)
      .style("opacity", 1);
  }

  function drawScholar() {
    binPlot = g
      .append("g")
      .attr("clip-path", "url(#clip)")
      .selectAll(".bin-group")
      .data(scholarData)
      .join("g")
      .attr("class", "bin-group");

    binPlot
      .append("rect")
      .attr("class", "scholar-rect")
      .attr("x", (d: ScholarData) => xScale(d.x))
      .attr("y", (d: ScholarData) => yScale(d.y))
      .attr("width", binSize * 2)
      .attr("height", binSize * 2)
      .attr("rx", Math.min(binSize / 5, 15))
      .attr("ry", Math.min(binSize / 5, 15))
      .attr("fill", function (d: ScholarData) {
        const totalPoints = d.data.length;
        let groupedByCluster = d3.group(d.data, (p) => p.cluster);

        groupedByCluster = new Map(
          Array.from(groupedByCluster).sort((a, b) => {
            return b[1].length - a[1].length;
          })
        );

        // @ts-ignore
        const defs = d3.select(this.parentNode).append("defs");
        let gradientId = `gradient-${Math.random().toString(36).slice(2, 9)}`;
        let gradient = defs
          .append("linearGradient")
          .attr("id", gradientId)
          .attr("x1", "0%")
          .attr("y1", "0%")
          .attr("x2", "100%")
          .attr("y2", "100%");

        if (totalPoints === 1) {
          return clusterColor(d.data[0].cluster.toString());
        }

        let accumulated = 0;
        groupedByCluster.forEach((value, key) => {
          const clusterSize = value.length;
          const portion = accumulated / totalPoints;
          const nextPortion = (accumulated + clusterSize) / totalPoints;
          gradient
            .append("stop")
            .attr("offset", `${portion * 100}%`)
            .attr("stop-color", clusterColor(key.toString()));
          gradient
            .append("stop")
            .attr("offset", `${nextPortion * 100}%`)
            .attr("stop-color", clusterColor(key.toString()));
          accumulated += clusterSize;
        });

        return `url(#${gradientId})`;
      })
      .on("mouseover", async function (event: any, d: any) {
        const titles = d.data.map((p: Data) => ({
          title: p.title,
          abstract: p.abstract.substring(0, 100), // Get the first 100 characters of the abstract
          cluster: p.cluster,
        }));

        titles.sort((a: Data, b: Data) => a.cluster - b.cluster);

        let tableHtml = "<table style='width: 100%; font-size: 10px;'>";
        for (const { title, abstract, cluster } of titles) {
          tableHtml += `<tr><td style="color: ${clusterColor(cluster.toString())}">${title}</td><td style="font-size: 8px">${abstract}</td></tr>`;
        }
        tableHtml += "</table></td></tr><tr><td colspan='2'><hr></td></tr>";
        tableHtml += "</table>";

        tooltipTimeout = setTimeout(() => {
          tooltip.transition().style("display", "block").style("opacity", 0.9);
          tooltip
            .html(`${tableHtml}`)
            .style("left", event.pageX - 10 + "px")
            .style("top", event.pageY - 28 + "px")
            .style("border", `1px solid #2C3E50`)
            .style("height", "300px")
            .style("overflow", "auto");
        }, 500);
      })
      .on("mouseleave", function (event: any, d: any) {
        clearTimeout(tooltipTimeout);
        tooltip.style("display", "none").style("opacity", 0);
      })
      // click and show all the paper position in dot
      .on("click", function (event: any, d: ScholarData) {
        tooltip.style("display", "none").style("opacity", 0);
        // all the other bin-group should be hidden
        // d3.selectAll(".bin-group").style("opacity", 0.1);

        d3.selectAll(".paper-dot").remove();
        console.log(d.data, d.x, d.y, xScale(d.x), yScale(d.y));

        //@ts-ignore
        d3.select(this.parentNode)
          .selectAll(".paper-dot")
          .data(d.data)
          .join("circle")
          .attr("class", "paper-dot")
          .attr("cx", (p: Data) => {
            console.log(p.umap_x, xScale(p.umap_x));
            return xScale(d.x) + p.umap_x * 2;
          })
          .attr("cy", (p: Data) => {
            console.log(p.umap_y, yScale(p.umap_y));
            return yScale(d.y) + p.umap_y * 2;
          })
          .attr("r", 2)
          .attr("fill", (p: Data) => clusterColor(p.cluster.toString()));
      })
      .style("opacity", 0)
      .transition()
      .duration(500)
      .delay(() => Math.random() * 200)
      .style("opacity", 0.8);

    // add scholar name
    binPlot
      .append("text")
      .attr("class", "scholar-name")
      .attr("x", (d: ScholarData) => xScale(d.x) - 5)
      .attr("y", (d: ScholarData) => yScale(d.y) - 1)
      .text((d: ScholarData) => d.name)
      .attr("fill", "#2C3E50")
      .style("font-size", "5px");
  }

  function updatePlot() {
    // remove all binGroup and draw new bins
    binPlot = d3.selectAll(".bin-group");
    binPlot.transition().duration(1000).attr("opacity", 0).remove();

    if (!scholarView) {
      drawBins();
    } else {
      scholarData = getScholarData(binData) as ScholarData[];
      scholarData = adjustScholars(scholarData, width, height, 100);
      drawScholar();
    }
  }

  function adjustBins(
    binData: any,
    width: number,
    height: number,
    padding: number
  ): BinData[] {
    // Filter out the bins that have no points
    binData = binData.filter((bin: BinData) => bin.data.length > 0);

    // Find the minimum and maximum bin coordinates
    const minX = d3.min(binData, (d: BinData) => d.x) as number;
    const maxX = d3.max(binData, (d: BinData) => d.x) as number;
    const minY = d3.min(binData, (d: BinData) => d.y) as number;
    const maxY = d3.max(binData, (d: BinData) => d.y) as number;

    // Normalize the bin coordinates to the range [0, 1]
    binData.forEach((bin: BinData) => {
      bin.x = (bin.x - minX) / (maxX - minX);
      bin.y = (bin.y - minY) / (maxY - minY);
    });

    width = window.innerWidth * 0.6 - margin.left - margin.right;
    // height using 100vh
    height = window.innerHeight * 0.9 - margin.top - margin.bottom;

    // Calculate the size of the bins
    let binSizeX = (width - padding) / (maxX - minX + 1);
    let binSizeY = (height - padding) / (maxY - minY + 1);

    binSizeX = Math.min(binSizeX, binSizeY) * 1.1;

    // Adjust the bin coordinates and size to avoid overlap and reduce white space
    binData.forEach((bin: BinData) => {
      bin.x = padding + bin.x * width;
      bin.y = padding + bin.y * (height - padding);
      bin.width = binSizeX;
      bin.height = Math.min(binSizeX, binSizeY);
    });

    // binSize = binSizeX;

    return binData;
  }

  function adjustScholars(
    scholarData: ScholarData[],
    width: number,
    height: number,
    padding: number
  ): ScholarData[] {
    // Find the minimum and maximum scholar coordinates
    const minX = d3.min(scholarData, (d: ScholarData) => d.x) as number;
    const maxX = d3.max(scholarData, (d: ScholarData) => d.x) as number;
    const minY = d3.min(scholarData, (d: ScholarData) => d.y) as number;
    const maxY = d3.max(scholarData, (d: ScholarData) => d.y) as number;

    // Normalize the scholar coordinates to the range [0, 1]
    scholarData.forEach((scholar: ScholarData) => {
      scholar.x = (scholar.x - minX) / (maxX - minX);
      scholar.y = (scholar.y - minY) / (maxY - minY);

      // Adjust umap_x and umap_y for all the Data objects
      // scholar.data.forEach((p: Data) => {
      //   p.umap_x = (p.umap_x - minX) / (maxX - minX);
      //   p.umap_y = (p.umap_y - minY) / (maxY - minY);
      // });
    });

    // Calculate the size of the scholars
    let scholarSizeX = (width - padding) / (maxX - minX + 1);
    let scholarSizeY = (height - padding) / (maxY - minY + 1);

    scholarSizeX = Math.min(scholarSizeX, scholarSizeY) * 1.1;

    // Adjust the scholar coordinates and size to avoid overlap and reduce white space
    scholarData.forEach((scholar: ScholarData) => {
      scholar.x = padding + scholar.x * (width - padding);
      scholar.y = padding + scholar.y * (height - padding);
    });

    return scholarData;
  }

  function groupByCluster(binData: BinData[]): any[] {
    const clusterMap = new Map();
    for (const bin of binData) {
      for (const point of bin.data) {
        if (!clusterMap.has(point.cluster)) {
          clusterMap.set(point.cluster, {
            cluster: point.cluster,
            keywords: point.top_keywords,
            x: [bin.x],
            y: [bin.y],
          });
        } else {
          clusterMap.get(point.cluster).x.push(bin.x);
          clusterMap.get(point.cluster).y.push(bin.y);
        }
      }
    }

    for (const clusterData of clusterMap.values()) {
      clusterData.x = d3.mean(clusterData.x);
      clusterData.y = d3.mean(clusterData.y);
    }

    return Array.from(clusterMap.values());
  }

  // utils function
  async function handleParamsChange() {
    const newData = await fetch("http://localhost:8000/update", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        binsNum: binsNum,
        clusterNum: clusterNum,
      }),
    }).then((res) => res.json());

    await loadData();
  }

  const selectAllBins = () => {
    if (!isSelectAll) {
      binData.forEach((bin: BinData) => {
        bin.selected = true;
      });
      selectedBins = binData;
      d3.selectAll(".rectBin").style("stroke", (d: any) =>
        d.selected ? "#2C3E50" : "none"
      );
      isSelectAll = true;
    } else {
      binData.forEach((bin: BinData) => {
        bin.selected = false;
      });
      selectedBins = [];
      d3.selectAll(".rectBin").style("stroke", (d: any) =>
        d.selected ? "#2C3E50" : "none"
      );

      isSelectAll = false;
    }
  };

  const handleSemanticRetrieval = async () => {
    clearTimeout(timeout);
    const query = searchTerm.trim();

    if (query.length < 3) {
      filteredBins = [];
      d3.selectAll(".rectBin").style("fill-opacity", 0.8);
      return;
    }

    if (query.length > 3) {
      timeout = setTimeout(() => {
        fetchSemanticRetrieval(query);
      }, 1000);
    }
  };

  const fetchSemanticRetrieval = async (query: string) => {
    await fetch("http://localhost:8000/retrieval", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query, user_id: userId }),
    })
      .then((res) => res.json())
      .then((data) => {
        data = JSON.parse(data);
        // highlight the matching bins
        // d3.selectAll(".rectBin").style("fill-opacity", 0.05);
        // d3.selectAll(".rectBin")
        //   .transition()
        //   .duration(500)
        //   .filter((d: any) => {
        //     return matchingBins.includes(d);
        //   })
        //   .style("fill-opacity", 1);

        // // also highlight the long-term-bin-keywords and bin-emoji
        // d3.selectAll(".bin-emoji").style("fill-opacity", 0.05);
        // d3.selectAll(".bin-emoji")
        //   .transition()
        //   .duration(500)
        //   .filter((d: any) => {
        //     return matchingBins.includes(d);
        //   })
        //   .style("fill-opacity", 1);

        // d3.selectAll(".long-term-bin-keywords").attr("style", "opacity: 0.01");
        // d3.selectAll(".long-term-bin-keywords")
        //   .transition()
        //   .duration(500)
        //   .filter((d: any) => {
        //     return matchingBins.includes(d);
        //   })
        //   .attr("style", "opacity: 1");
      });
  };

  const handleKeywordSearch = async () => {
    const query = searchTerm.trim().toLowerCase();

    if (query.length < 3) {
      filteredBins = [];
      d3.selectAll(".rectBin").style("fill-opacity", 0.95);
      d3.selectAll(".scholar-rect").style("fill-opacity", 0.85);
      d3.selectAll(".scholar-name").style("fill-opacity", 0.85);
      return;
    }

    if (query.length > 3) {
      if (scholarView) {
        const matchingScholars = scholarData.filter((scholar: ScholarData) => {
          console.log(
            scholar.name.toLowerCase().trim(),
            query,
            scholar.name.toLowerCase().trim().includes(query)
          );

          let searchableString = [
            scholar.name.toLowerCase().trim(),
            typeof scholar.faculty === "string"
              ? scholar.faculty.toLowerCase().trim()
              : "",
            typeof scholar.department === "string"
              ? scholar.department.toLowerCase().trim()
              : "",
            typeof scholar.area_of_focus === "string"
              ? scholar.area_of_focus.toLowerCase().trim()
              : "",
          ].join(" ");

          return searchableString.includes(query);
        });

        filteredScholars = matchingScholars;
        console.log(matchingScholars);
        d3.selectAll(".scholar-rect").style("fill-opacity", 0.05);
        d3.selectAll(".scholar-name").style("fill-opacity", 0.05);
        d3.selectAll(".scholar-rect")
          .filter((d: any) => {
            console.log(d);
            return matchingScholars.includes(d);
          })
          .transition()
          .duration(500)
          .style("fill-opacity", 1);

        d3.selectAll(".scholar-name")
          .filter((d: any) => {
            return matchingScholars.includes(d);
          })
          .transition()
          .duration(500)
          .style("fill-opacity", 1);
      } else {
        const matchingBins = binData.filter((bin: BinData) => {
          const binData = bin.data;
          for (const data of binData) {
            if (
              data.email.toLowerCase().includes(query) ||
              data.first_name.toLowerCase().includes(query) ||
              data.last_name.toLowerCase().includes(query) ||
              data.title.toLowerCase().includes(query) ||
              data.abstract.toLowerCase().includes(query)
            ) {
              return true;
            }
          }
          return false;
        });

        filteredBins = matchingBins;
        d3.selectAll(".rectBin").style("fill-opacity", 0.05);
        d3.selectAll(".rectBin")
          .filter((d: any) => {
            return matchingBins.includes(d);
          })
          .style("fill-opacity", 1);
      }
    }
  };

  const handleBinsNumChange = async () => {
    binData = constructBinData(data);
    binData = adjustBins(binData, width, height, 100);
    redraw();
  };

  const getScholarData = (binData: BinData[]): ScholarData[] => {
    const scholarData = {} as any;

    binData.forEach((bin) => {
      bin.data.forEach((p) => {
        const name = `${p.first_name} ${p.last_name}`;
        if (!scholarData[name]) {
          scholarData[name] = {
            id: p.author_id,
            name: name,
            x: 0,
            y: 0,
            faculty: p.faculty,
            department: p.department,
            area_of_focus: p.area_of_focus,
            gs_link: p.gs_link,
            author_id: p.author_id,
            email: p.email,
            data: [],
            count: 0,
          };
        }
        scholarData[name].x += p.umap_x;
        scholarData[name].y += p.umap_y;
        scholarData[name].data.push(p);
        scholarData[name].count++;
      });
    });

    // Calculate mean umap_x and umap_y
    for (const name in scholarData) {
      scholarData[name].x /= scholarData[name].count;
      scholarData[name].y /= scholarData[name].count;
    }

    return Object.values(scholarData);
  };

  function toggleView() {
    scholarView = !scholarView;
    updatePlot();
  }

  function handleHighlightReferences(event: CustomEvent) {
    const references = event.detail as RefereneceType[];
    const paperIds = references.map((r) => r.paper_id);
    console.log(references, paperIds);

    // highlight bins that contain the references
    if (scholarView) {
      d3.selectAll(".scholar-rect").style("fill-opacity", 0.05);
      d3.selectAll(".scholar-name").style("fill-opacity", 0.05);
      d3.selectAll(".scholar-rect")
        .filter((d: any) => {
          return d.data.some((p: Data) =>
            paperIds.includes(p.paper_id.toString())
          );
        })
        .transition()
        .duration(500)
        .style("fill-opacity", 1);

      d3.selectAll(".scholar-name")
        .filter((d: any) => {
          return d.data.some((p: Data) =>
            paperIds.includes(p.paper_id.toString())
          );
        })
        .transition()
        .duration(500)
        .style("fill-opacity", 1);
    } else {
      d3.selectAll(".rectBin").style("fill-opacity", 0.05);
      d3.selectAll(".rectBin")
        .filter((d: any) => {
          return d.data.some((p: Data) =>
            paperIds.includes(p.paper_id.toString())
          );
        })
        .transition()
        .duration(500)
        .style("fill-opacity", 1);
    }
  }


  function handleCitationClick(event: CustomEvent) {
    const paperId = event.detail;
    if (scholarView) {
      d3.selectAll(".scholar-rect").style("stroke", "none");
      d3.selectAll(".scholar-rect")
        .filter((d: any) => {
          return d.data.some((p: Data) => p.paper_id.toString() === paperId);
        })
        .style("stroke", "#34495e")
        .style("stroke-width", 2);
    } else {
      d3.selectAll(".rectBin").style("stroke", "none");
      d3.selectAll(".rectBin")
        .filter((d: any) => {
          return d.data.some((p: Data) => p.paper_id.toString() === paperId);
        })
        .style("stroke", "#34495e")
        .style("stroke-width", 2);
    }
  }

  async function loadData() {
    userId = localStorage.getItem("userId") as string;
    const dataFrame = await fetch(`http://localhost:8000/data`).then((res) =>
      res.json()
    );

    data = dataFrame.df;
    binData = constructBinData(data);
    binData = adjustBins(binData, width, height, 100);
  }

  if (browser) {
    onMount(async () => {
      console.log(
        longTermVis.clientWidth,
        longTermVis.clientHeight,
        width,
        height
      );
      width = longTermVis.clientWidth;
      await loadData();
    });
  }

  $: if (browser && data) redraw();
  $: if (browser && binData && binData.length > 0)
    searchTerm, handleKeywordSearch();

  $: if (browser && binData && binData.length > 0)
    binsNum, handleBinsNumChange();
</script>

<div>
  <div id="memolet">
    <div id="long-term-container">
      <div class="control-panel">
        <input
          type="text"
          bind:value={searchTerm}
          placeholder="Keyword search"
        />
        <!-- <button on:click={handleSemanticRetrieval}>Search</button> -->

        <label for="binsNum">Bins number:</label>
        <input
          type="range"
          id="binsNum"
          name="binsNum"
          min="10"
          max="39"
          step="2"
          bind:value={binsNum}
        />
        <span class="indicator">{binsNum}</span>

        <!-- <label for="clusterNum">Cluster number:</label> -->
        <!-- <input
        type="range"
        id="clusterNum"
        name="clusterNum"
        min="2"
        max="10"
        bind:value={clusterNum}
      />
      <span class="indicator">{clusterNum}</span> -->
        <!-- <button on:click={handleParamsChange} disabled>Apply</button> -->

        <!-- a switch button, toggle isScholarView -->
        <label class="switch">
          <input
            type="checkbox"
            id="scholarView"
            bind:checked={scholarView}
            on:click={toggleView}
          />
          <span class="slider round"></span>
        </label>
        <label for="scholarView"
          >{scholarView ? "Paper View" : "Scholar View"}</label
        >

        <!-- <button on:click={selectAllBins}
        >{isSelectAll ? "Unselect All" : "Select All"}</button
      > -->
      </div>
      <div id="long-term-vis" bind:this={longTermVis}></div>
    </div>

    <div id="chat-container">
      <!-- {#if binData?.length > 0 && scholarData?.length > 0} -->
        <Chat
          {scholarView}
          {selectedBins}
          {binData}
          {scholarData}
          on:retrievedReferences={handleHighlightReferences}
          on:citationClick="{handleCitationClick}"
        />
      <!-- {/if} -->
    </div>
  </div>
</div>

<style>
  #memolet {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: stretch;
  }

  #long-term-vis {
    width: 100%;
    height: 100%;
    z-index: 1;
  }

  #long-term-container {
    flex: 0.68;
  }

  #chat-container {
    /* margin-left: 1rem; */
    flex: 0.32;
  }

  .control-panel {
    display: flex;
    width: 95%;
    align-items: center;
    gap: 20px;
    padding: 10px;
    background-color: #ecf0f1;
    border-radius: 5px;
    box-shadow: 5px 4px 6px 0px rgba(44, 62, 80, 0.1);
  }

  .control-panel input[type="text"] {
    padding: 5px;
    border: 1px solid #ddd;
    border-radius: 5px;
    width: 50%; /* Adjust the width as needed */
  }

  .control-panel input[type="text"]:focus {
    outline-color: #2980b9;
    border-color: #349bdb;
  }

  .control-panel input[type="range"] {
    padding: 5px;
    border: 1px solid #ddd;
    border-radius: 5px;
    width: 25%; /* Adjust the width as needed */
  }
  .control-panel input[type="range"]::-webkit-slider-thumb {
    background-color: #349bdb;
  }

  .control-panel input[type="range"]::-moz-range-thumb {
    background-color: #349bdb;
  }

  .control-panel input[type="text"]:focus {
    border-color: #349bdb;
  }

  .control-panel input[type="checkbox"] {
    width: 20%;
  }

  .control-panel button {
    padding: 5px;
    background-color: #349bdb;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
  }

  .control-panel button:hover {
    background-color: #2980b9;
  }

  .control-panel .indicator {
    font-weight: bold;
    color: #2980b9;
  }

  .indicator {
    margin: 0 5px;
  }

  #long-term-vis {
    display: flex;
    flex-direction: column;
  }
  .switch {
    position: relative;
    display: inline-block;
    width: 60px;
    height: 24px;
  }

  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    -webkit-transition: 0.4s;
    transition: 0.4s;
  }

  .slider:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    -webkit-transition: 0.4s;
    transition: 0.4s;
  }

  input:checked + .slider {
    background-color: #349bdb;
  }

  input:focus + .slider {
    box-shadow: 0 0 1px #349bdb;
  }

  input:checked + .slider:before {
    -webkit-transform: translateX(30px);
    -ms-transform: translateX(30px);
    transform: translateX(30px);
  }

  /* Rounded sliders */
  .slider.round {
    border-radius: 34px;
  }

  .slider.round:before {
    border-radius: 50%;
  }
</style>
