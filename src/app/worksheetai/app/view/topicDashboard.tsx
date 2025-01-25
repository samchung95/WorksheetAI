import React, { useState, useEffect, FC, MouseEvent } from 'react';
import { Code2, FileText, Plus, Minus, Check } from 'lucide-react';

interface Topic {
  id: number;
  name: string;
  difficulty: 'easy' | 'medium' | 'hard';
  description: string;
}

type Language = 'python' | 'javascript';

const TOPICS_DATA: Record<Language, Topic[]> = {
  python: [
    { id: 1, name: 'Variables and Data Types', difficulty: 'easy', description: 'Learn about variables and basic data types in Python' },
    { id: 2, name: 'Control Structures', difficulty: 'medium', description: 'Master if statements, loops, and control flow' },
    { id: 3, name: 'Functions', difficulty: 'hard', description: 'Understanding functions and their usage' },
    { id: 4, name: 'Lists and Arrays', difficulty: 'easy', description: 'Working with sequential data structures' }
  ],
  javascript: [
    { id: 5, name: 'Variables and Types', difficulty: 'easy', description: 'JavaScript variables and data types' },
    { id: 6, name: 'Functions and Scope', difficulty: 'medium', description: 'Functions, scope, and closures' },
    { id: 7, name: 'DOM Manipulation', difficulty: 'hard', description: 'Interacting with the Document Object Model' }
  ]
};

interface Distribution {
  easy: number;
  medium: number;
  hard: number;
}

interface SliderProps {
  topic: Topic;
  totalQuestions: number;
  distribution: Distribution;
  onDistributionChange: (dist: Distribution) => void;
}

const DifficultyDistributionSlider: FC<SliderProps> = ({
  topic,
  totalQuestions,
  distribution,
  onDistributionChange
}) => {
  const [activeThumb, setActiveThumb] = useState<'easy' | 'medium' | null>(null);
  
  const canHaveEasy = topic.difficulty === 'easy';
  const canHaveMedium = topic.difficulty !== 'hard';

  const handleMouseDown = (difficulty: 'easy' | 'medium') => (e: React.MouseEvent) => {
    setActiveThumb(difficulty);
    e.preventDefault();
  };

  const handleMouseMove = (e: globalThis.MouseEvent) => {
    if (!activeThumb) return;

    const slider = document.querySelector('.distribution-slider')?.getBoundingClientRect();
    if (!slider) return;

    const percentage = Math.min(Math.max(((e.clientX - slider.left) / slider.width) * 100, 0), 100);
    const questionValue = Math.round((percentage / 100) * totalQuestions);

    const newDist = calculateNewDistribution(questionValue);
    onDistributionChange(newDist);
  };

  const calculateNewDistribution = (value: number): Distribution => {
    let newDist = { ...distribution };

    if (activeThumb === 'easy') {
      newDist.easy = Math.min(value, totalQuestions - distribution.hard);
      newDist.medium = totalQuestions - newDist.easy - distribution.hard;
    } else if (activeThumb === 'medium') {
      newDist.medium = Math.max(0, Math.min(
        value - distribution.easy,
        totalQuestions - distribution.easy - distribution.hard
      ));
      newDist.hard = totalQuestions - distribution.easy - newDist.medium;
    }

    // Ensure non-negative values
    Object.keys(newDist).forEach(k => newDist[k as keyof Distribution] = Math.max(0, newDist[k as keyof Distribution]));
    
    // Adjust for rounding errors
    const diff = totalQuestions - Object.values(newDist).reduce((a, b) => a + b, 0);
    if (diff !== 0) {
      if (activeThumb === 'easy') newDist.medium += diff;
      else if (activeThumb === 'medium') newDist.hard += diff;
    }

    return newDist;
  };

  useEffect(() => {
    const cleanup = () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', cleanup);
    };

    if (activeThumb) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', cleanup);
    }
    return cleanup;
  }, [activeThumb]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">Question Distribution</span>
        <div className="flex space-x-2">
          {canHaveEasy && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Easy: {distribution.easy}
            </span>
          )}
          {canHaveMedium && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              Medium: {distribution.medium}
            </span>
          )}
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Hard: {distribution.hard}
          </span>
        </div>
      </div>

      <div className="relative h-6 bg-gray-200 rounded-lg cursor-pointer distribution-slider">
        {canHaveEasy && (
          <div
            className="absolute h-full bg-green-200 rounded-l-lg transition-all"
            style={{ width: `${(distribution.easy / totalQuestions) * 100}%` }}
          >
            <div
              className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 bg-green-500 rounded-full cursor-grab active:cursor-grabbing -translate-x-1/2"
              onMouseDown={handleMouseDown('easy')}
            />
          </div>
        )}

        {canHaveMedium && (
          <div
            className="absolute h-full bg-yellow-200 transition-all"
            style={{ 
              left: `${(distribution.easy / totalQuestions) * 100}%`,
              width: `${(distribution.medium / totalQuestions) * 100}%`
            }}
          >
            <div
              className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 bg-yellow-500 rounded-full cursor-grab active:cursor-grabbing -translate-x-1/2"
              onMouseDown={handleMouseDown('medium')}
            />
          </div>
        )}

        <div
          className="absolute h-full bg-red-200 rounded-r-lg transition-all"
          style={{ 
            left: `${((distribution.easy + distribution.medium) / totalQuestions) * 100}%`,
            width: `${(distribution.hard / totalQuestions) * 100}%`
          }}
        />

        <div className="absolute w-full h-full flex justify-between px-2 text-xs text-gray-500 -bottom-6">
          <span>0</span>
          <span>{Math.floor(totalQuestions / 2)}</span>
          <span>{totalQuestions}</span>
        </div>
      </div>
    </div>
  );
};

const TopicsDashboard: FC = () => {
  const [selectedLanguage, setSelectedLanguage] = useState<Language>('python');
  const [selectedTopics, setSelectedTopics] = useState<Set<number>>(new Set());
  const [topicQuestions, setTopicQuestions] = useState<Record<number, number>>({});
  const [topicDistributions, setTopicDistributions] = useState<Record<number, Distribution>>({});

  const handleTopicSelect = (topic: Topic, isSelected: boolean) => {
    const newSelected = new Set(selectedTopics);
    if (isSelected) {
      newSelected.add(topic.id);
      const questions = 5;
      setTopicQuestions(prev => ({ ...prev, [topic.id]: questions }));
      
      const baseDist: Distribution = topic.difficulty === 'easy' ? 
        { easy: 3, medium: 1, hard: 1 } :
        topic.difficulty === 'medium' ?
        { easy: 0, medium: 3, hard: 2 } :
        { easy: 0, medium: 0, hard: 5 };
      
      setTopicDistributions(prev => ({ ...prev, [topic.id]: baseDist }));
    } else {
      newSelected.delete(topic.id);
      const { [topic.id]: _, ...restQ } = topicQuestions;
      const { [topic.id]: __, ...restD } = topicDistributions;
      setTopicQuestions(restQ);
      setTopicDistributions(restD);
    }
    setSelectedTopics(newSelected);
  };

  const handleDistributionChange = (topicId: number, dist: Distribution) => {
    setTopicDistributions(prev => ({ ...prev, [topicId]: dist }));
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Coding Topics Dashboard</h1>
        <p className="text-gray-600">Select topics and customize question distribution</p>
      </div>

      <div className="flex space-x-4 mb-6">
        {Object.keys(TOPICS_DATA).map(lang => (
          <button
            key={lang}
            onClick={() => setSelectedLanguage(lang as Language)}
            className={`px-4 py-2 rounded-lg ${
              selectedLanguage === lang 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {lang.charAt(0).toUpperCase() + lang.slice(1)}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4">
        {TOPICS_DATA[selectedLanguage].map(topic => (
          <TopicCard
            key={topic.id}
            topic={topic}
            isSelected={selectedTopics.has(topic.id)}
            onSelect={handleTopicSelect}
            questions={topicQuestions[topic.id] || 5}
            distribution={topicDistributions[topic.id] || { easy: 0, medium: 0, hard: 0 }}
            onDistributionChange={dist => handleDistributionChange(topic.id, dist)}
          />
        ))}
      </div>

      {selectedTopics.size > 0 && <SelectedSummary selectedTopics={selectedTopics} />}
    </div>
  );
};

interface TopicCardProps {
  topic: Topic;
  isSelected: boolean;
  onSelect: (topic: Topic, selected: boolean) => void;
  questions: number;
  distribution: Distribution;
  onDistributionChange: (dist: Distribution) => void;
}

const TopicCard: FC<TopicCardProps> = ({
  topic: Topic;
  isSelected: boolean;
  onSelect: (topic: Topic, selected: boolean) => void;
  questions: number;
  distribution: Distribution;
  onDistributionChange: (dist: Distribution) => void;
}> = ({ topic, isSelected, onSelect, questions, distribution, onDistributionChange }) => {
  const difficultyColor = {
    easy: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    hard: 'bg-red-100 text-red-800'
  }[topic.difficulty];

  return (
    <div className={`p-4 rounded-lg border ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <Code2 className="w-5 h-5 text-gray-500" />
          <div>
            <h3 className="font-medium">{topic.name}</h3>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${difficultyColor}`}>
              {topic.difficulty}
            </span>
          </div>
        </div>
        <button
          onClick={() => onSelect(topic, !isSelected)}
          className={`px-3 py-1 rounded-lg flex items-center space-x-1 ${
            isSelected ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {isSelected ? (
            <>
              <Check className="w-4 h-4" />
              <span>Selected</span>
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              <span>Select</span>
            </>
          )}
        </button>
      </div>

      {isSelected && (
        <div className="mt-4 space-y-6">
          <QuestionCounter 
            count={questions}
            onChange={newCount => onDistributionChange({
              ...distribution,
              easy: Math.round(newCount * 0.6),
              medium: Math.round(newCount * 0.3),
              hard: newCount - Math.round(newCount * 0.6) - Math.round(newCount * 0.3)
            })}
          />
          <DifficultyDistributionSlider
            topic={topic}
            totalQuestions={questions}
            distribution={distribution}
            onDistributionChange={onDistributionChange}
          />
        </div>
      )}
    </div>
  );
};

interface QuestionCounterProps {
  count: number;
  onChange: (newCount: number) => void;
}

const QuestionCounter: FC<QuestionCounterProps> = ({
  count: number;
  onChange: (newCount: number) => void;
}> = ({ count, onChange }) => (
  <div>
    <div className="flex items-center justify-between mb-2">
      <label className="text-sm font-medium">Number of Questions</label>
      <div className="flex items-center space-x-2">
        <button
          onClick={() => onChange(Math.max(1, count - 1))}
          className="p-1 rounded-lg hover:bg-gray-100"
        >
          <Minus className="w-4 h-4" />
        </button>
        <span className="w-8 text-center">{count}</span>
        <button
          onClick={() => onChange(Math.min(20, count + 1))}
          className="p-1 rounded-lg hover:bg-gray-100"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
);

interface SelectedSummaryProps {
  selectedTopics: Set<number>;
}

const SelectedSummary: FC<SelectedSummaryProps> = ({ selectedTopics }) => (
  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
    <h2 className="text-lg font-medium mb-4">Selected Topics Summary</h2>
    <div className="space-y-4">
      {Array.from(selectedTopics).map(id => (
        <div key={id} className="flex items-center justify-between">
          <span className="text-sm font-medium">Topic ID: {id}</span>
          <span className="text-sm text-gray-500">Questions: {Math.floor(Math.random() * 15) + 5}</span>
        </div>
      ))}
    </div>
    <div className="mt-6 flex justify-end">
      <button
        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center space-x-2"
        onClick={() => console.log('Generating worksheet...')}
      >
        <FileText className="w-4 h-4" />
        <span>Generate Worksheet</span>
      </button>
    </div>
  </div>
);

export default TopicsDashboard;
