// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
    integrations: [
        starlight({
            title: 'Qai AgentOS',
            social: [
                { label: 'GitHub', href: 'https://github.com/Kayariyan28/Qai-AI-AgentOS', icon: 'github' },
            ],
            sidebar: [
                {
                    label: 'Start Here',
                    items: [
                        { label: 'User Guide', slug: 'guides/user-guide' },
                    ],
                },
                {
                    label: 'Capabilities',
                    items: [
                        { label: 'macOS Integration', slug: 'guides/macos-integration' },
                    ],
                },
                {
                    label: 'Reference',
                    autogenerate: { directory: 'reference' },
                },
                {
                    label: 'About',
                    items: [
                        { label: 'Vision', slug: 'about/vision' },
                        { label: 'PRD', slug: 'about/prd' },
                    ]
                }
            ],
            customCss: [
                './src/styles/custom.css',
            ],
        }),
    ],

    vite: {
        plugins: [tailwindcss()],
    },
});