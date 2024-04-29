<script>
	import Header from './Header.svelte';
	import './styles.css';
</script>

<div class="app">
	<!-- <Header /> -->

	<main>
		<slot />
	</main>

	<!-- <footer>
		<p>All rights reserved</p>
	</footer> -->
</div>

<style>
	.app {
		min-height: 100vh;
	}

	main {
		padding: 1rem;
		/* width: 100%; */
		margin: 0 auto;
		overflow: hidden;
	}

	footer {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		padding: 12px;
	}

	footer a {
		font-weight: bold;
	}

	@media (min-width: 480px) {
		footer {
			padding: 12px 0;
		}
	}
</style>
