<template>
  <div class="min-h-screen relative overflow-hidden">
    <div class="pointer-events-none absolute inset-0">
      <div class="absolute left-[-8rem] top-[-5rem] h-72 w-72 rounded-full bg-primary-fixed/45 blur-3xl" />
      <div class="absolute bottom-[-6rem] right-[-4rem] h-80 w-80 rounded-full bg-tertiary-fixed/45 blur-3xl" />
      <div class="absolute inset-0 ether-grid opacity-25" />
    </div>
    <slot />
  </div>
</template>
