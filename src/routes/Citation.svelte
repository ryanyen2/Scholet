<script lang="ts">
  import { createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher();

  export let id: string | undefined;
  export let gradient: string | undefined;

  function handleClick() {
    dispatch("click", id);
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Enter") {
      handleClick();
    }
  }
</script>

<span
  class="citation-bin-{id}"
  style="background: {gradient}; color: white; padding: 0.1em 0.5em; border-radius: 0.2em; cursor: pointer;"
  on:click={handleClick}
  on:keydown={handleKeydown}
  tabindex="0"
  role="button"
>
  {id}
</span>
