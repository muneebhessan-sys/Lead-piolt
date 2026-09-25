import { useState, useCallback, useEffect, useRef } from 'react';

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  shortcut?: string;
  section?: string;
  icon?: React.ReactNode;
  action: () => void;
  keywords?: string[];
}

interface UseCommandPaletteOptions {
  items: CommandItem[];
  triggerKeys?: string[];
  openOnMount?: boolean;
}

export function useCommandPalette({ items, triggerKeys = ['k', 'meta+k', 'ctrl+k'], openOnMount = false }: UseCommandPaletteOptions) {
  const [isOpen, setIsOpen] = useState(openOnMount);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [filteredItems, setFilteredItems] = useState<CommandItem[]>(items);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    const filtered = items
      .filter(item => {
        if (!query) return true;
        const search = query.toLowerCase();
        const haystack = [item.label, item.description, item.section, ...(item.keywords || [])].join(' ').toLowerCase();
        return haystack.includes(search);
      })
      .slice(0, 8);
    setFilteredItems(filtered);
    setSelectedIndex(0);
  }, [items, query]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && triggerKeys.includes(event.key.toLowerCase())) {
        event.preventDefault();
        setIsOpen(true);
      }
      if (event.key === 'Escape') {
        setIsOpen(false);
        setQuery('');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [triggerKeys]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 0);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  useEffect(() => {
    const selectedItem = listRef.current?.querySelector('[data-selected="true"]');
    selectedItem?.scrollIntoView({ block: 'nearest' });
  }, [selectedIndex]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, filteredItems.length - 1));
        break;
      case 'ArrowUp':
        event.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        event.preventDefault();
        filteredItems[selectedIndex]?.action();
        setIsOpen(false);
        setQuery('');
        break;
      case 'Escape':
        setIsOpen(false);
        setQuery('');
        break;
    }
  }, [filteredItems, selectedIndex]);

  const handleItemClick = useCallback((item: CommandItem) => {
    item.action();
    setIsOpen(false);
    setQuery('');
  }, []);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => { setIsOpen(false); setQuery(''); }, []);

  return {
    isOpen,
    query,
    setQuery,
    selectedIndex,
    filteredItems,
    inputRef,
    listRef,
    handleKeyDown,
    handleItemClick,
    open,
    close,
  };
}